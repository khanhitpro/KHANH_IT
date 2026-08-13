import os
import sys
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from tkinter import messagebox, filedialog

import customtkinter as ctk
from PIL import Image, ImageTk

APP_NAME = "KHÁNH IT - AI IMAGE CREATOR V4.1 CPU"
MODEL_ID = "segmind/tiny-sd"

def writable_root():
    local = os.getenv("LOCALAPPDATA")
    if local:
        p = Path(local) / "KHANH_IT_AI_IMAGE_CREATOR_V4"
    else:
        p = Path.home() / "KHANH_IT_AI_IMAGE_CREATOR_V4"
    p.mkdir(parents=True, exist_ok=True)
    return p

ROOT = writable_root()
OUTPUT = ROOT / "generated_images"
CACHE = ROOT / "models"
OUTPUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x760")
        self.minsize(1000, 680)

        self.pipe = None
        self.current_image = None
        self.preview_photo = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_left()
        self.build_right()

    def build_left(self):
        left = ctk.CTkScrollableFrame(self, width=390, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            left, text="KHÁNH IT", font=ctk.CTkFont(size=32, weight="bold")
        ).pack(anchor="w", padx=24, pady=(24, 0))
        ctk.CTkLabel(
            left, text="AI IMAGE CREATOR V4.1 CPU",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color="#4da3ff"
        ).pack(anchor="w", padx=24)
        ctk.CTkLabel(
            left, text="FREE LOCAL • Không API Key • Chạy bằng CPU",
            text_color="gray65"
        ).pack(anchor="w", padx=24, pady=(0, 20))

        ctk.CTkLabel(left, text="MÔ TẢ ẢNH", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=24, pady=(0, 6)
        )
        self.prompt = ctk.CTkTextbox(left, height=190, wrap="word")
        self.prompt.pack(fill="x", padx=24)
        self.prompt.insert(
            "1.0",
            "A cinematic landscape of Ha Long Bay at sunset, beautiful light, "
            "high detail, wide angle, no text"
        )

        ctk.CTkLabel(left, text="KÍCH THƯỚC TẠO", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=24, pady=(18, 6)
        )
        self.size = ctk.CTkComboBox(
            left,
            values=["512x512", "768x512 (ngang)", "512x768 (dọc)"],
            state="readonly"
        )
        self.size.set("768x512 (ngang)")
        self.size.pack(fill="x", padx=24)

        ctk.CTkLabel(left, text="SỐ BƯỚC AI", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=24, pady=(16, 6)
        )
        self.steps = ctk.CTkComboBox(
            left, values=["2", "3", "4", "6", "8"], state="readonly"
        )
        self.steps.set("4")
        self.steps.pack(fill="x", padx=24)

        ctk.CTkLabel(
            left,
            text="Ít bước = nhanh hơn. CPU nên dùng 2–4 bước.",
            text_color="gray55"
        ).pack(anchor="w", padx=24, pady=(5, 12))

        self.load_btn = ctk.CTkButton(
            left, text="⬇ TẢI / NẠP MODEL AI",
            height=42, command=self.start_load
        )
        self.load_btn.pack(fill="x", padx=24, pady=(6, 8))

        self.generate_btn = ctk.CTkButton(
            left, text="✨ TẠO ẢNH MIỄN PHÍ",
            height=50, state="disabled",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_generate
        )
        self.generate_btn.pack(fill="x", padx=24, pady=8)

        self.status = ctk.CTkLabel(
            left,
            text="Bấm TẢI / NẠP MODEL AI ở lần chạy đầu tiên.",
            text_color="gray65",
            wraplength=340
        )
        self.status.pack(fill="x", padx=24, pady=12)

        ctk.CTkLabel(
            left,
            text="Lần đầu cần Internet để tải model.\nSau khi tải xong có thể dùng lại từ bộ nhớ máy.",
            text_color="gray50",
            justify="left"
        ).pack(anchor="w", padx=24, pady=(5, 20))

    def build_right(self):
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(right, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="XEM TRƯỚC ẢNH",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.save_btn = ctk.CTkButton(
            top, text="Lưu thành...", state="disabled", command=self.save_as
        )
        self.save_btn.grid(row=0, column=1, padx=4)

        ctk.CTkButton(
            top, text="Mở thư mục ảnh", command=self.open_folder
        ).grid(row=0, column=2, padx=(4, 0))

        frame = ctk.CTkFrame(right, fg_color="#111927")
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.preview_frame = frame

        self.preview = ctk.CTkLabel(
            frame,
            text="Ảnh AI sẽ hiển thị tại đây",
            text_color="gray55",
            font=ctk.CTkFont(size=18)
        )
        self.preview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def start_load(self):
        self.load_btn.configure(state="disabled")
        self.status.configure(text="Đang tải/nạp model AI. Lần đầu có thể mất vài phút...")
        threading.Thread(target=self.load_model, daemon=True).start()

    def load_model(self):
        try:
            import torch
            from diffusers import StableDiffusionPipeline

            torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))

            self.pipe = StableDiffusionPipeline.from_pretrained(
                MODEL_ID,
                cache_dir=str(CACHE),
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            self.pipe = self.pipe.to("cpu")
            self.pipe.enable_attention_slicing()

            self.after(0, self.model_ready)
        except Exception as e:
            error_text = str(e)
            self.after(0, lambda msg=error_text: self.load_failed(msg))

    def model_ready(self):
        self.load_btn.configure(state="normal", text="✓ MODEL ĐÃ SẴN SÀNG")
        self.generate_btn.configure(state="normal")
        self.status.configure(
            text="Model đã sẵn sàng. Nhập mô tả rồi bấm TẠO ẢNH MIỄN PHÍ."
        )

    def load_failed(self, error):
        self.load_btn.configure(state="normal")
        self.status.configure(text="Không nạp được model.")
        messagebox.showerror("Lỗi model AI", error)

    def start_generate(self):
        if self.pipe is None:
            messagebox.showwarning("Model", "Hãy nạp model AI trước.")
            return

        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Thiếu mô tả", "Hãy nhập mô tả ảnh.")
            return

        self.generate_btn.configure(state="disabled", text="ĐANG TẠO...")
        self.status.configure(text="CPU đang tạo ảnh. Vui lòng chờ...")
        threading.Thread(target=self.generate, args=(prompt,), daemon=True).start()

    def generate(self, prompt):
        try:
            import torch

            selected = self.size.get()
            if selected.startswith("768x512"):
                width, height = 768, 512
            elif selected.startswith("512x768"):
                width, height = 512, 768
            else:
                width, height = 512, 512

            result = self.pipe(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=int(self.steps.get()),
                guidance_scale=1.0
            )

            image = result.images[0].convert("RGB")
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = OUTPUT / f"AI_CPU_{stamp}.png"
            image.save(path, "PNG")

            self.current_image = image
            self.current_path = path
            self.after(0, self.done)
        except Exception as e:
            error_text = str(e)
            self.after(0, lambda msg=error_text: self.generate_failed(msg))

    def done(self):
        self.generate_btn.configure(state="normal", text="✨ TẠO ẢNH MIỄN PHÍ")
        self.save_btn.configure(state="normal")
        self.status.configure(text=f"Hoàn tất: {self.current_path.name}")
        self.show_preview()

    def generate_failed(self, error):
        self.generate_btn.configure(state="normal", text="✨ TẠO ẢNH MIỄN PHÍ")
        self.status.configure(text="Tạo ảnh thất bại.")
        messagebox.showerror("Lỗi tạo ảnh", error)

    def show_preview(self):
        if self.current_image is None:
            return

        self.update_idletasks()
        img = self.current_image.copy()
        max_w = max(self.preview_frame.winfo_width() - 50, 400)
        max_h = max(self.preview_frame.winfo_height() - 50, 350)
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview.configure(image=self.preview_photo, text="")

    def save_as(self):
        if self.current_image is None:
            return

        path = filedialog.asksaveasfilename(
            title="Lưu ảnh",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        if not path:
            return

        if path.lower().endswith((".jpg", ".jpeg")):
            self.current_image.save(path, "JPEG", quality=95)
        else:
            self.current_image.save(path, "PNG")

    def open_folder(self):
        try:
            if os.name == "nt":
                os.startfile(OUTPUT)
            else:
                subprocess.Popen(["xdg-open", str(OUTPUT)])
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


if __name__ == "__main__":
    App().mainloop()
