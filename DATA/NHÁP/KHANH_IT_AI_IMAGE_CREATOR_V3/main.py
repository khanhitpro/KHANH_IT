import os
import io
import json
import base64
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk
from openai import OpenAI

APP_NAME = "KHÁNH IT - AI IMAGE CREATOR V3"
OUTPUT_DIR = Path("generated_images")
DATA_DIR = Path("app_data")
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

PRESETS = {
    "Tự do": "",
    "Hình nền TV 16:9": (
        "Tạo hình nền TV tỉ lệ 16:9, bố cục cân đối, hình ảnh sắc nét, "
        "chi tiết cao, ánh sáng đẹp, phù hợp hiển thị trên TV 4K. "
        "Không chèn chữ trừ khi người dùng yêu cầu. "
    ),
    "Banner quảng cáo 16:9": (
        "Thiết kế banner quảng cáo tỉ lệ 16:9, hiện đại, chuyên nghiệp, "
        "chủ thể nổi bật, bố cục rõ ràng, khoảng trống hợp lý cho nội dung. "
    ),
    "Logo / Icon 1:1": (
        "Thiết kế logo/icon tỉ lệ 1:1, dễ nhận diện, sạch, hiện đại, "
        "đường nét rõ ràng, phù hợp làm icon ứng dụng. "
    ),
    "Quảng cáo sản phẩm": (
        "Tạo ảnh quảng cáo sản phẩm cao cấp, sản phẩm là chủ thể chính, "
        "ánh sáng studio, bố cục thương mại chuyên nghiệp, cực kỳ sắc nét. "
    ),
    "Phong cảnh điện ảnh": (
        "Tạo ảnh phong cảnh điện ảnh, ánh sáng ấn tượng, chiều sâu tốt, "
        "siêu chi tiết, chân thực, màu sắc hài hòa. "
    ),
    "Ảnh chân dung": (
        "Tạo ảnh chân dung chuyên nghiệp, ánh sáng đẹp, da tự nhiên, "
        "chi tiết rõ, bố cục cân đối, hậu cảnh phù hợp. "
    ),
}

SIZE_CHOICES = {
    "Tự động": "auto",
    "1024×1024 - Vuông": "1024x1024",
    "1536×1024 - Ngang": "1536x1024",
    "1024×1536 - Dọc": "1024x1536",
    "2048×2048 - 2K Vuông": "2048x2048",
    "2048×1152 - 2K 16:9": "2048x1152",
    "1920×1088 - 16:9": "1920x1088",
    "1088×1920 - 9:16": "1088x1920",
    "2560×1440 - QHD": "2560x1440",
    "3840×2160 - 4K": "3840x2160",
    "2160×3840 - 4K Dọc": "2160x3840",
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_NAME)
        self.geometry("1440x900")
        self.minsize(1180, 760)

        self.images = []
        self.image_paths = []
        self.current_index = 0
        self.preview_photo = None

        self.reference_paths = []
        self.history = self.load_json(HISTORY_FILE, [])
        self.settings = self.load_json(SETTINGS_FILE, {})

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_workspace()
        self.apply_saved_settings()
        self.refresh_history()

    # ----------------------------------------------------------
    # UI
    # ----------------------------------------------------------

    def build_sidebar(self):
        self.sidebar = ctk.CTkScrollableFrame(
            self, width=430, corner_radius=0, fg_color="#0b111b"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="KHÁNH IT",
            font=ctk.CTkFont(size=34, weight="bold"),
        ).pack(anchor="w", padx=25, pady=(24, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="AI IMAGE CREATOR V3",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#4da3ff"
        ).pack(anchor="w", padx=25, pady=(0, 2))

        ctk.CTkLabel(
            self.sidebar,
            text="Tạo • Chỉnh sửa • Ảnh tham chiếu • 4K",
            text_color="gray65"
        ).pack(anchor="w", padx=25, pady=(0, 18))

        self.section("KẾT NỐI")

        self.api_entry = ctk.CTkEntry(
            self.sidebar,
            placeholder_text="OpenAI API Key",
            show="•",
            height=38
        )
        self.api_entry.pack(fill="x", padx=25, pady=(0, 7))

        api_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        api_row.pack(fill="x", padx=25, pady=(0, 10))
        api_row.grid_columnconfigure((0, 1), weight=1)

        self.show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            api_row,
            text="Hiện key",
            variable=self.show_key_var,
            command=self.toggle_key
        ).grid(row=0, column=0, sticky="w")

        self.save_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            api_row,
            text="Lưu key trên máy",
            variable=self.save_key_var
        ).grid(row=0, column=1, sticky="e")

        self.model_combo = ctk.CTkComboBox(
            self.sidebar,
            values=["gpt-image-2", "gpt-image-1.5", "gpt-image-1"],
            state="readonly",
            height=36
        )
        self.model_combo.set("gpt-image-2")
        self.model_combo.pack(fill="x", padx=25, pady=(0, 14))

        self.section("YÊU CẦU ẢNH")

        self.preset_combo = ctk.CTkComboBox(
            self.sidebar,
            values=list(PRESETS.keys()),
            state="readonly",
            command=self.on_preset,
            height=36
        )
        self.preset_combo.set("Hình nền TV 16:9")
        self.preset_combo.pack(fill="x", padx=25, pady=(0, 8))

        self.prompt_box = ctk.CTkTextbox(self.sidebar, height=145, wrap="word")
        self.prompt_box.pack(fill="x", padx=25, pady=(0, 8))
        self.prompt_box.insert(
            "1.0",
            "Vịnh Hạ Long lúc hoàng hôn, mặt nước phản chiếu ánh nắng, "
            "góc rộng điện ảnh, không chữ."
        )

        quick = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        quick.pack(fill="x", padx=25, pady=(0, 12))
        quick.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            quick, text="Xóa prompt", command=self.clear_prompt, height=32
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            quick, text="Prompt gần nhất", command=self.use_last_prompt, height=32
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.section("CẤU HÌNH TẠO ẢNH")

        self.size_combo = ctk.CTkComboBox(
            self.sidebar,
            values=list(SIZE_CHOICES.keys()),
            state="readonly",
            height=36
        )
        self.size_combo.set("1920×1088 - 16:9")
        self.size_combo.pack(fill="x", padx=25, pady=(0, 8))

        row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=(0, 8))
        row.grid_columnconfigure((0, 1, 2), weight=1)

        self.quality_combo = ctk.CTkComboBox(
            row, values=["auto", "low", "medium", "high"], state="readonly"
        )
        self.quality_combo.set("medium")
        self.quality_combo.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.count_combo = ctk.CTkComboBox(
            row, values=["1", "2", "3", "4"], state="readonly"
        )
        self.count_combo.set("1")
        self.count_combo.grid(row=0, column=1, sticky="ew", padx=4)

        self.format_combo = ctk.CTkComboBox(
            row, values=["PNG", "JPG", "WEBP"], state="readonly"
        )
        self.format_combo.set("PNG")
        self.format_combo.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="Chất lượng             Số ảnh             Định dạng",
            text_color="gray50",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=28, pady=(0, 9))

        self.generate_btn = ctk.CTkButton(
            self.sidebar,
            text="✨  TẠO ẢNH AI",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_generate
        )
        self.generate_btn.pack(fill="x", padx=25, pady=(2, 12))

        self.section("ẢNH THAM CHIẾU / CHỈNH SỬA")

        ref_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        ref_row.pack(fill="x", padx=25, pady=(0, 8))
        ref_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            ref_row,
            text="＋ Thêm ảnh",
            command=self.add_reference_images
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            ref_row,
            text="Xóa ảnh tham chiếu",
            command=self.clear_references
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.ref_label = ctk.CTkLabel(
            self.sidebar,
            text="Chưa có ảnh tham chiếu",
            text_color="gray60",
            wraplength=360
        )
        self.ref_label.pack(fill="x", padx=25, pady=(0, 8))

        self.edit_btn = ctk.CTkButton(
            self.sidebar,
            text="🪄  CHỈNH / BIẾN ĐỔI BẰNG AI",
            height=44,
            command=self.start_edit
        )
        self.edit_btn.pack(fill="x", padx=25, pady=(0, 12))

        self.status = ctk.CTkLabel(
            self.sidebar,
            text="Sẵn sàng",
            text_color="gray65",
            wraplength=360
        )
        self.status.pack(fill="x", padx=25, pady=(2, 18))

    def build_workspace(self):
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(right, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="KHÔNG GIAN LÀM VIỆC",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        actions = ctk.CTkFrame(top, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")

        self.prev_btn = ctk.CTkButton(
            actions, text="◀", width=42, state="disabled", command=self.prev_image
        )
        self.prev_btn.pack(side="left", padx=3)

        self.next_btn = ctk.CTkButton(
            actions, text="▶", width=42, state="disabled", command=self.next_image
        )
        self.next_btn.pack(side="left", padx=3)

        self.save_btn = ctk.CTkButton(
            actions, text="Lưu thành...", width=105, state="disabled", command=self.save_as
        )
        self.save_btn.pack(side="left", padx=3)

        self.reuse_btn = ctk.CTkButton(
            actions, text="Dùng lại prompt", width=115, command=self.use_last_prompt
        )
        self.reuse_btn.pack(side="left", padx=3)

        ctk.CTkButton(
            actions, text="Mở thư mục", width=105, command=self.open_output
        ).pack(side="left", padx=(3, 0))

        self.preview_frame = ctk.CTkFrame(right, fg_color="#111927")
        self.preview_frame.grid(row=1, column=0, sticky="nsew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.preview = ctk.CTkLabel(
            self.preview_frame,
            text="Ảnh được tạo hoặc chỉnh sửa sẽ hiển thị ở đây",
            text_color="gray50",
            font=ctk.CTkFont(size=18)
        )
        self.preview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        bottom = ctk.CTkFrame(right, height=205)
        bottom.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        bottom.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(bottom, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 3))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="LỊCH SỬ GẦN ĐÂY",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="Xóa lịch sử",
            width=90,
            height=28,
            command=self.clear_history
        ).grid(row=0, column=1, sticky="e")

        self.history_box = ctk.CTkTextbox(bottom, height=150, wrap="word")
        self.history_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.history_box.configure(state="disabled")

    def section(self, text):
        ctk.CTkLabel(
            self.sidebar,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4da3ff"
        ).pack(anchor="w", padx=25, pady=(6, 7))

    # ----------------------------------------------------------
    # Settings
    # ----------------------------------------------------------

    def apply_saved_settings(self):
        env_key = os.getenv("OPENAI_API_KEY", "")
        saved_key = self.settings.get("api_key", "")
        if env_key:
            self.api_entry.insert(0, env_key)
        elif saved_key:
            self.api_entry.insert(0, saved_key)
            self.save_key_var.set(True)

        model = self.settings.get("model")
        if model in ["gpt-image-2", "gpt-image-1.5", "gpt-image-1"]:
            self.model_combo.set(model)

    def save_settings(self):
        data = {
            "model": self.model_combo.get(),
            "api_key": self.api_entry.get().strip() if self.save_key_var.get() else ""
        }
        SETTINGS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ----------------------------------------------------------
    # Prompt / presets
    # ----------------------------------------------------------

    def on_preset(self, choice):
        if choice in ("Hình nền TV 16:9", "Banner quảng cáo 16:9"):
            self.size_combo.set("1920×1088 - 16:9")
        elif choice == "Logo / Icon 1:1":
            self.size_combo.set("1024×1024 - Vuông")
        elif choice == "Ảnh chân dung":
            self.size_combo.set("1024×1536 - Dọc")

    def full_prompt(self):
        user_text = self.prompt_box.get("1.0", "end").strip()
        return (PRESETS.get(self.preset_combo.get(), "") + user_text).strip()

    def clear_prompt(self):
        self.prompt_box.delete("1.0", "end")

    def use_last_prompt(self):
        if not self.history:
            messagebox.showinfo("Lịch sử", "Chưa có prompt nào trong lịch sử.")
            return

        prompt = self.history[0].get("user_prompt") or self.history[0].get("prompt", "")
        self.prompt_box.delete("1.0", "end")
        self.prompt_box.insert("1.0", prompt)

    # ----------------------------------------------------------
    # Reference images
    # ----------------------------------------------------------

    def add_reference_images(self):
        files = filedialog.askopenfilenames(
            title="Chọn ảnh tham chiếu",
            filetypes=[
                ("Ảnh", "*.png *.jpg *.jpeg *.webp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WEBP", "*.webp"),
            ]
        )
        if not files:
            return

        for f in files:
            p = Path(f)
            if p not in self.reference_paths:
                self.reference_paths.append(p)

        self.update_reference_label()

        try:
            img = Image.open(self.reference_paths[0]).convert("RGB")
            self.images = [img]
            self.image_paths = [self.reference_paths[0]]
            self.current_index = 0
            self.show_current()
        except Exception:
            pass

    def clear_references(self):
        self.reference_paths = []
        self.update_reference_label()

    def update_reference_label(self):
        if not self.reference_paths:
            self.ref_label.configure(text="Chưa có ảnh tham chiếu")
            return

        names = ", ".join(p.name for p in self.reference_paths[:3])
        extra = len(self.reference_paths) - 3
        if extra > 0:
            names += f" +{extra} ảnh"
        self.ref_label.configure(
            text=f"{len(self.reference_paths)} ảnh: {names}"
        )

    # ----------------------------------------------------------
    # Generate
    # ----------------------------------------------------------

    def start_generate(self):
        if not self.validate_common():
            return
        self.save_settings()
        self.set_busy(True, "AI đang tạo ảnh...")
        threading.Thread(target=self.generate_worker, daemon=True).start()

    def generate_worker(self):
        try:
            client = OpenAI(api_key=self.api_entry.get().strip())
            model = self.model_combo.get()
            size = self.get_api_size(model)
            quality = self.quality_combo.get()
            count = int(self.count_combo.get())
            output_format = self.api_output_format()

            result = client.images.generate(
                model=model,
                prompt=self.full_prompt(),
                size=size,
                quality=quality,
                n=count,
                output_format=output_format
            )

            images, paths = self.decode_and_save(result.data, "AI", output_format)
            self.images = images
            self.image_paths = paths
            self.current_index = 0

            self.add_history(
                action="TẠO",
                user_prompt=self.prompt_box.get("1.0", "end").strip(),
                full_prompt=self.full_prompt(),
                paths=paths,
                model=model,
                size=size
            )
            self.after(0, self.finish_success)

        except Exception as e:
            self.after(0, lambda: self.fail(str(e)))

    # ----------------------------------------------------------
    # Edit
    # ----------------------------------------------------------

    def start_edit(self):
        if not self.validate_common():
            return
        if not self.reference_paths:
            messagebox.showwarning(
                "Thiếu ảnh tham chiếu",
                "Hãy chọn ít nhất một ảnh trước khi dùng chức năng chỉnh sửa."
            )
            return

        self.save_settings()
        self.set_busy(True, "AI đang chỉnh sửa ảnh...")
        threading.Thread(target=self.edit_worker, daemon=True).start()

    def edit_worker(self):
        files = []
        try:
            client = OpenAI(api_key=self.api_entry.get().strip())
            model = self.model_combo.get()
            size = self.get_api_size(model)
            quality = self.quality_combo.get()
            count = int(self.count_combo.get())
            output_format = self.api_output_format()

            for path in self.reference_paths:
                files.append(open(path, "rb"))

            kwargs = {
                "model": model,
                "image": files if len(files) > 1 else files[0],
                "prompt": self.full_prompt(),
                "size": size,
                "quality": quality,
                "n": count,
                "output_format": output_format,
            }

            # GPT Image 2 automatically processes image inputs at high fidelity.
            if model != "gpt-image-2":
                kwargs["input_fidelity"] = "high"

            result = client.images.edit(**kwargs)

            images, paths = self.decode_and_save(result.data, "EDIT", output_format)
            self.images = images
            self.image_paths = paths
            self.current_index = 0

            self.add_history(
                action="SỬA",
                user_prompt=self.prompt_box.get("1.0", "end").strip(),
                full_prompt=self.full_prompt(),
                paths=paths,
                model=model,
                size=size
            )
            self.after(0, self.finish_success)

        except Exception as e:
            self.after(0, lambda: self.fail(str(e)))
        finally:
            for f in files:
                try:
                    f.close()
                except Exception:
                    pass

    # ----------------------------------------------------------
    # Decode / save
    # ----------------------------------------------------------

    def decode_and_save(self, data, prefix, output_format):
        images = []
        paths = []
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        ext_map = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}
        ext = ext_map[output_format]

        for i, item in enumerate(data, start=1):
            raw = base64.b64decode(item.b64_json)
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            path = OUTPUT_DIR / f"{prefix}_{stamp}_{i}{ext}"
            self.save_image(img, path, output_format)
            images.append(img)
            paths.append(path)

        return images, paths

    @staticmethod
    def save_image(img, path, fmt):
        if fmt == "jpeg":
            img.convert("RGB").save(path, "JPEG", quality=95)
        elif fmt == "webp":
            img.save(path, "WEBP", quality=95)
        else:
            img.save(path, "PNG")

    # ----------------------------------------------------------
    # Preview
    # ----------------------------------------------------------

    def finish_success(self):
        self.set_busy(False, f"Hoàn tất {len(self.images)} ảnh.")
        self.save_btn.configure(state="normal")
        self.update_nav()
        self.show_current()
        self.refresh_history()

    def show_current(self):
        if not self.images:
            return

        img = self.images[self.current_index].copy()
        self.update_idletasks()

        max_w = max(self.preview_frame.winfo_width() - 60, 420)
        max_h = max(self.preview_frame.winfo_height() - 80, 360)
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        self.preview_photo = ImageTk.PhotoImage(img)
        path = self.image_paths[self.current_index] if self.image_paths else None
        name = path.name if path else ""

        self.preview.configure(
            image=self.preview_photo,
            text=f"\n{name}\n{self.current_index + 1}/{len(self.images)}",
            compound="top"
        )
        self.update_nav()

    def update_nav(self):
        state = "normal" if len(self.images) > 1 else "disabled"
        self.prev_btn.configure(state=state)
        self.next_btn.configure(state=state)

    def prev_image(self):
        if self.images:
            self.current_index = (self.current_index - 1) % len(self.images)
            self.show_current()

    def next_image(self):
        if self.images:
            self.current_index = (self.current_index + 1) % len(self.images)
            self.show_current()

    def save_as(self):
        if not self.images:
            return

        fmt = self.api_output_format()
        ext_map = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}
        ext = ext_map[fmt]

        path = filedialog.asksaveasfilename(
            title="Lưu ảnh",
            defaultextension=ext,
            filetypes=[("Ảnh", f"*{ext}")]
        )
        if not path:
            return

        try:
            self.save_image(self.images[self.current_index], Path(path), fmt)
            messagebox.showinfo("Thành công", f"Đã lưu ảnh:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    # ----------------------------------------------------------
    # History
    # ----------------------------------------------------------

    def add_history(self, action, user_prompt, full_prompt, paths, model, size):
        self.history.insert(0, {
            "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "action": action,
            "user_prompt": user_prompt,
            "prompt": full_prompt,
            "paths": [str(p) for p in paths],
            "model": model,
            "size": size,
        })
        self.history = self.history[:100]
        HISTORY_FILE.write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def refresh_history(self):
        lines = []
        for item in self.history[:10]:
            text = item.get("user_prompt") or item.get("prompt", "")
            text = text.replace("\n", " ")
            if len(text) > 100:
                text = text[:100] + "..."

            lines.append(
                f'[{item.get("time", "")}] {item.get("action", "")} | '
                f'{item.get("model", "")} | {item.get("size", "")}\n'
                f'{text}\n'
            )

        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        self.history_box.insert(
            "1.0",
            "\n".join(lines) if lines else "Chưa có lịch sử."
        )
        self.history_box.configure(state="disabled")

    def clear_history(self):
        if not self.history:
            return
        if messagebox.askyesno("Xóa lịch sử", "Xóa toàn bộ lịch sử tạo ảnh?"):
            self.history = []
            HISTORY_FILE.write_text("[]", encoding="utf-8")
            self.refresh_history()

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def validate_common(self):
        if not self.api_entry.get().strip():
            messagebox.showwarning("Thiếu API key", "Vui lòng nhập OpenAI API key.")
            return False
        if not self.full_prompt():
            messagebox.showwarning("Thiếu mô tả", "Vui lòng nhập yêu cầu tạo/chỉnh ảnh.")
            return False
        return True

    def get_api_size(self, model):
        selected = SIZE_CHOICES[self.size_combo.get()]

        if model == "gpt-image-2":
            return selected

        # Legacy GPT Image models use standard documented sizes.
        if selected == "auto":
            return "auto"

        if selected in ("1024x1024", "1536x1024", "1024x1536"):
            return selected

        try:
            w, h = map(int, selected.split("x"))
            if w == h:
                return "1024x1024"
            return "1536x1024" if w > h else "1024x1536"
        except Exception:
            return "auto"

    def api_output_format(self):
        return {
            "PNG": "png",
            "JPG": "jpeg",
            "WEBP": "webp"
        }[self.format_combo.get()]

    def set_busy(self, busy, text):
        state = "disabled" if busy else "normal"
        self.generate_btn.configure(state=state)
        self.edit_btn.configure(state=state)
        self.status.configure(text=text)

    def fail(self, error):
        self.set_busy(False, "Có lỗi xảy ra.")
        messagebox.showerror("Lỗi AI", error)

    def toggle_key(self):
        self.api_entry.configure(show="" if self.show_key_var.get() else "•")

    @staticmethod
    def load_json(path, default):
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return default

    def open_output(self):
        OUTPUT_DIR.mkdir(exist_ok=True)
        path = OUTPUT_DIR.resolve()
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.name == "posix":
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


if __name__ == "__main__":
    app = App()
    app.mainloop()
