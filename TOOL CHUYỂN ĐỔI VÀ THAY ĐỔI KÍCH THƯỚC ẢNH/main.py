import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageColor, ImageOps

# =========================================================
# CẤU HÌNH KÍCH THƯỚC ẢNH
# =========================================================

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
TARGET_SIZE = (TARGET_WIDTH, TARGET_HEIGHT)

# Các kích thước chuẩn nhúng vào file ICO
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


class PNGConverterTool:
    def __init__(self, root):
        self.root = root
        self.root.title("KHÁNH IT - CHUYỂN ĐỔI ẢNH PNG / ICO / JPG")
        self.root.geometry("780x690")
        self.root.minsize(720, 630)

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.resize_mode = tk.StringVar(value="crop")
        self.output_format = tk.StringVar(value="PNG")
        self.background_color = tk.StringVar(value="#000000")
        self.jpg_quality = tk.IntVar(value=95)

        self.is_running = False

        self.create_interface()

    # =====================================================
    # GIAO DIỆN
    # =====================================================

    def create_interface(self):
        header_frame = tk.Frame(self.root, bg="#111827", height=90)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="KHÁNH IT - PNG IMAGE & ICON CONVERTER",
            font=("Arial", 19, "bold"),
            fg="#38BDF8",
            bg="#111827",
        ).pack(pady=(14, 2))

        tk.Label(
            header_frame,
            text="Chuyển PNG sang 16:9 (1080p) • Chuyển PNG sang ICO Windows",
            font=("Arial", 11),
            fg="white",
            bg="#111827",
        ).pack()

        content_frame = tk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=25, pady=18)

        # =================================================
        # THƯ MỤC NGUỒN
        # =================================================

        tk.Label(
            content_frame,
            text="Thư mục chứa ảnh PNG:",
            font=("Arial", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        input_frame = tk.Frame(content_frame)
        input_frame.pack(fill="x", pady=(5, 12))

        tk.Entry(
            input_frame, textvariable=self.input_folder, font=("Arial", 10)
        ).pack(side="left", fill="x", expand=True, ipady=7)

        tk.Button(
            input_frame,
            text="CHỌN THƯ MỤC",
            width=16,
            command=self.select_input_folder,
        ).pack(side="left", padx=(8, 0), ipady=4)

        # =================================================
        # THƯ MỤC ĐẦU RA
        # =================================================

        tk.Label(
            content_frame,
            text="Thư mục lưu ảnh đã chuyển đổi:",
            font=("Arial", 11, "bold"),
            anchor="w",
        ).pack(fill="x")

        output_frame = tk.Frame(content_frame)
        output_frame.pack(fill="x", pady=(5, 12))

        tk.Entry(
            output_frame, textvariable=self.output_folder, font=("Arial", 10)
        ).pack(side="left", fill="x", expand=True, ipady=7)

        tk.Button(
            output_frame,
            text="CHỌN THƯ MỤC",
            width=16,
            command=self.select_output_folder,
        ).pack(side="left", padx=(8, 0), ipady=4)

        # =================================================
        # CHẾ ĐỘ XỬ LÝ (CHỈ ÁP DỤNG CHO PNG & JPG 16:9)
        # =================================================

        self.mode_frame = tk.LabelFrame(
            content_frame,
            text=" Chế độ điều chỉnh ảnh (Áp dụng cho PNG / JPG) ",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=8,
        )
        self.mode_frame.pack(fill="x", pady=(0, 12))

        tk.Radiobutton(
            self.mode_frame,
            text="Cắt đầy khung 1920 × 1080 – Không làm méo ảnh",
            variable=self.resize_mode,
            value="crop",
            font=("Arial", 10),
        ).pack(anchor="w", pady=2)

        tk.Radiobutton(
            self.mode_frame,
            text="Giữ toàn bộ nội dung ảnh – Tự động thêm nền",
            variable=self.resize_mode,
            value="contain",
            font=("Arial", 10),
        ).pack(anchor="w", pady=2)

        tk.Radiobutton(
            self.mode_frame,
            text="Kéo giãn trực tiếp về 1920 × 1080 – Có thể làm méo",
            variable=self.resize_mode,
            value="stretch",
            font=("Arial", 10),
        ).pack(anchor="w", pady=2)

        # =================================================
        # ĐỊNH DẠNG ĐẦU RA
        # =================================================

        settings_frame = tk.LabelFrame(
            content_frame,
            text=" Cài đặt đầu ra ",
            font=("Arial", 11, "bold"),
            padx=12,
            pady=10,
        )
        settings_frame.pack(fill="x", pady=(0, 12))

        format_row = tk.Frame(settings_frame)
        format_row.pack(fill="x", pady=3)

        tk.Label(
            format_row,
            text="Định dạng:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left")

        format_combo = ttk.Combobox(
            format_row,
            textvariable=self.output_format,
            values=("PNG", "JPG", "ICO"),
            state="readonly",
            width=12,
        )
        format_combo.pack(side="left")
        format_combo.bind("<<ComboboxSelected>>", self.update_format_status)

        self.quality_label = tk.Label(
            format_row, text="Chất lượng JPG:", font=("Arial", 10, "bold")
        )
        self.quality_label.pack(side="left", padx=(30, 8))

        self.quality_spinbox = tk.Spinbox(
            format_row,
            from_=50,
            to=100,
            textvariable=self.jpg_quality,
            width=6,
            justify="center",
        )
        self.quality_spinbox.pack(side="left")

        self.percent_label = tk.Label(
            format_row, text="%", font=("Arial", 10)
        )
        self.percent_label.pack(side="left", padx=(3, 0))

        color_row = tk.Frame(settings_frame)
        color_row.pack(fill="x", pady=(8, 3))

        self.color_title = tk.Label(
            color_row,
            text="Màu nền:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w",
        )
        self.color_title.pack(side="left")

        self.color_entry = tk.Entry(
            color_row,
            textvariable=self.background_color,
            width=14,
            justify="center",
            font=("Consolas", 10),
        )
        self.color_entry.pack(side="left", ipady=3)

        self.color_hint = tk.Label(
            color_row,
            text="Ví dụ: #000000 là đen, #FFFFFF là trắng (dành cho JPG & Contain)",
            font=("Arial", 9),
            fg="#555555",
        )
        self.color_hint.pack(side="left", padx=(12, 0))

        # =================================================
        # TIẾN TRÌNH
        # =================================================

        self.progress_bar = ttk.Progressbar(
            content_frame, orient="horizontal", mode="determinate"
        )
        self.progress_bar.pack(fill="x", pady=(2, 6))

        self.status_label = tk.Label(
            content_frame,
            text="Sẵn sàng xử lý.",
            font=("Arial", 10, "bold"),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(0, 6))

        # =================================================
        # NHẬT KÝ
        # =================================================

        log_frame = tk.Frame(content_frame)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame,
            height=7,
            font=("Consolas", 9),
            state="disabled",
            wrap="word",
        )
        self.log_box.pack(side="left", fill="both", expand=True)

        log_scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=log_scrollbar.set)

        # =================================================
        # NÚT BẮT ĐẦU
        # =================================================

        bottom_frame = tk.Frame(self.root, bg="#E5E7EB")
        bottom_frame.pack(side="bottom", fill="x")

        self.start_button = tk.Button(
            bottom_frame,
            text="▶ BẮT ĐẦU CHUYỂN ĐỔI",
            font=("Arial", 13, "bold"),
            bg="#0284C7",
            fg="white",
            activebackground="#0369A1",
            activeforeground="white",
            cursor="hand2",
            command=self.start_processing,
        )
        self.start_button.pack(fill="x", padx=25, pady=14, ipady=9)

        self.update_format_status()

    # =====================================================
    # CHỌN THƯ MỤC
    # =====================================================

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh PNG")
        if not folder:
            return

        self.input_folder.set(folder)
        self.sync_output_folder()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu file")
        if folder:
            self.output_folder.set(folder)

    def sync_output_folder(self):
        input_folder = self.input_folder.get().strip()
        if not input_folder or not os.path.isdir(input_folder):
            return

        output_format = self.output_format.get().upper()
        if output_format == "JPG":
            folder_name = "PNG_TO_JPG_1920X1080"
        elif output_format == "ICO":
            folder_name = "PNG_TO_ICO"
        else:
            folder_name = "PNG_1920X1080"

        self.output_folder.set(os.path.join(input_folder, folder_name))

    def update_format_status(self, event=None):
        output_format = self.output_format.get().upper()

        if output_format == "JPG":
            self.quality_spinbox.config(state="normal")
            self.color_entry.config(state="normal")
        elif output_format == "ICO":
            self.quality_spinbox.config(state="disabled")
            self.color_entry.config(state="disabled")
        else:
            self.quality_spinbox.config(state="disabled")
            self.color_entry.config(state="normal")

        self.sync_output_folder()

    # =====================================================
    # NHẬT KÝ
    # =====================================================

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def write_log(self, message):
        self.log_box.config(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # =====================================================
    # BẮT ĐẦU XỬ LÝ
    # =====================================================

    def start_processing(self):
        if self.is_running:
            return

        input_folder = self.input_folder.get().strip()
        output_folder = self.output_folder.get().strip()
        output_format = self.output_format.get().upper()

        if not input_folder:
            messagebox.showwarning("Thiếu thư mục", "Vui lòng chọn thư mục chứa ảnh PNG.")
            return

        if not os.path.isdir(input_folder):
            messagebox.showerror("Thư mục không tồn tại", "Thư mục chứa ảnh PNG không tồn tại.")
            return

        if not output_folder:
            messagebox.showwarning("Thiếu thư mục đầu ra", "Vui lòng chọn thư mục lưu kết quả.")
            return

        if output_format != "ICO":
            try:
                ImageColor.getrgb(self.background_color.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Màu nền không hợp lệ",
                    "Vui lòng nhập mã màu dạng HEX (ví dụ: #000000 hoặc #FFFFFF).",
                )
                return

        if output_format == "JPG":
            try:
                quality = int(self.jpg_quality.get())
                if quality < 50 or quality > 100:
                    raise ValueError
            except (ValueError, tk.TclError):
                messagebox.showerror("Chất lượng không hợp lệ", "Chất lượng JPG phải từ 50 đến 100.")
                return

        self.is_running = True
        self.clear_log()
        self.progress_bar["value"] = 0
        self.start_button.config(state="disabled", text="ĐANG XỬ LÝ...")
        self.status_label.config(text="Đang tìm ảnh PNG trong thư mục...")

        threading.Thread(target=self.process_images, daemon=True).start()

    # =====================================================
    # TIẾN TRÌNH XỬ LÝ HÀNG LOẠT
    # =====================================================

    def process_images(self):
        input_folder = self.input_folder.get().strip()
        output_folder = self.output_folder.get().strip()
        output_format = self.output_format.get().upper()

        try:
            os.makedirs(output_folder, exist_ok=True)

            png_files = [
                f for f in os.listdir(input_folder)
                if os.path.isfile(os.path.join(input_folder, f)) and f.lower().endswith(".png")
            ]
            png_files.sort()

            if not png_files:
                self.root.after(0, self.no_png_found)
                return

            total_files = len(png_files)
            success_count = 0
            error_count = 0

            self.root.after(0, lambda: self.progress_bar.config(maximum=total_files))
            self.root.after(0, self.write_log, f"Tìm thấy {total_files} file PNG.")
            self.root.after(0, self.write_log, f"Định dạng đích: {output_format}")
            if output_format == "ICO":
                self.root.after(0, self.write_log, "Kích thước Icon: Đa phân giải (16px → 256px)")
            else:
                self.root.after(0, self.write_log, "Kích thước: 1920 × 1080 (16:9)")
            self.root.after(0, self.write_log, "--------------------------------------------")

            for index, file_name in enumerate(png_files, start=1):
                input_path = os.path.join(input_folder, file_name)
                original_name = os.path.splitext(file_name)[0]

                if output_format == "JPG":
                    output_name = original_name + ".jpg"
                elif output_format == "ICO":
                    output_name = original_name + ".ico"
                else:
                    output_name = original_name + ".png"

                output_path = self.create_unique_output_path(
                    output_folder, output_name, input_path
                )

                try:
                    self.convert_image(input_path, output_path, output_format)
                    success_count += 1
                    self.root.after(
                        0,
                        self.write_log,
                        f"[THÀNH CÔNG] {file_name} → {os.path.basename(output_path)}",
                    )
                except Exception as error:
                    error_count += 1
                    self.root.after(0, self.write_log, f"[LỖI] {file_name}: {error}")

                self.root.after(0, self.update_progress, index, total_files, file_name)

            self.root.after(
                0,
                self.processing_complete,
                success_count,
                error_count,
                output_folder,
                output_format,
            )

        except Exception as error:
            err_msg = str(error)
            self.root.after(0, lambda: messagebox.showerror("Lỗi xử lý", err_msg))
        finally:
            self.root.after(0, self.reset_button)

    # =====================================================
    # CHUYỂN ĐỔI ẢNH ĐƠN LẺ
    # =====================================================

    def convert_image(self, input_path, output_path, output_format):
        with Image.open(input_path) as original_image:
            image = ImageOps.exif_transpose(original_image).convert("RGBA")

            # XỬ LÝ RIÊNG CHO ĐỊNH DẠNG ICO
            if output_format == "ICO":
                # Giữ nguyên tỉ lệ vuông cho icon bằng contain vào khung 256x256, giữ kênh trong suốt
                ico_base = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                fitted_icon = ImageOps.contain(
                    image, (256, 256), method=Image.Resampling.LANCZOS
                )
                paste_x = (256 - fitted_icon.width) // 2
                paste_y = (256 - fitted_icon.height) // 2
                ico_base.alpha_composite(fitted_icon, (paste_x, paste_y))

                # Lưu đa tầng kích thước chuẩn Windows
                ico_base.save(output_path, format="ICO", sizes=ICO_SIZES)
                return

            # XỬ LÝ CHO PNG / JPG 16:9
            background_rgb = ImageColor.getrgb(self.background_color.get().strip())
            resize_mode = self.resize_mode.get()

            if resize_mode == "crop":
                output_image = ImageOps.fit(
                    image,
                    TARGET_SIZE,
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
            elif resize_mode == "contain":
                resized_image = ImageOps.contain(
                    image, TARGET_SIZE, method=Image.Resampling.LANCZOS
                )
                output_image = Image.new(
                    "RGBA", TARGET_SIZE, background_rgb + (255,)
                )
                paste_x = (TARGET_WIDTH - resized_image.width) // 2
                paste_y = (TARGET_HEIGHT - resized_image.height) // 2
                output_image.alpha_composite(resized_image, (paste_x, paste_y))
            else:
                output_image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

            if output_format == "JPG":
                jpg_background = Image.new("RGB", TARGET_SIZE, background_rgb)
                if output_image.mode == "RGBA":
                    jpg_background.paste(
                        output_image, (0, 0), output_image.getchannel("A")
                    )
                else:
                    jpg_background.paste(output_image.convert("RGB"), (0, 0))

                jpg_background.save(
                    output_path,
                    format="JPEG",
                    quality=int(self.jpg_quality.get()),
                    optimize=True,
                    progressive=True,
                    subsampling=0,
                )
            else:
                output_image.save(
                    output_path,
                    format="PNG",
                    optimize=True,
                    compress_level=6,
                )

    # =====================================================
    # HÀM BỔ TRỢ & GIAO DIỆN
    # =====================================================

    @staticmethod
    def create_unique_output_path(output_folder, output_name, input_path):
        output_path = os.path.join(output_folder, output_name)
        if os.path.abspath(output_path).lower() != os.path.abspath(input_path).lower():
            return output_path

        base_name, extension = os.path.splitext(output_name)
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = os.path.join(output_folder, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def update_progress(self, current, total, file_name):
        self.progress_bar["value"] = current
        self.status_label.config(text=f"Đang xử lý {current}/{total}: {file_name}")

    def no_png_found(self):
        self.status_label.config(text="Không tìm thấy ảnh PNG.")
        messagebox.showwarning(
            "Không có ảnh PNG", "Không tìm thấy file .png trong thư mục đã chọn."
        )

    def processing_complete(self, success_count, error_count, output_folder, output_format):
        self.progress_bar["value"] = self.progress_bar["maximum"]
        self.status_label.config(
            text=f"Hoàn thành: {success_count} thành công, {error_count} lỗi."
        )
        self.write_log("--------------------------------------------")
        self.write_log(
            f"Hoàn thành: {success_count} file thành công, {error_count} file lỗi."
        )

        res = messagebox.askyesno(
            "Hoàn thành",
            f"Đã xử lý xong!\n\n"
            f"Định dạng đầu ra: {output_format}\n"
            f"Thành công: {success_count} file\n"
            f"Lỗi: {error_count} file\n\n"
            f"Bạn có muốn mở thư mục lưu file không?",
        )
        if res:
            os.startfile(output_folder)

    def reset_button(self):
        self.is_running = False
        self.start_button.config(state="normal", text="▶ BẮT ĐẦU CHUYỂN ĐỔI")


if __name__ == "__main__":
    root = tk.Tk()
    app = PNGConverterTool(root)
    root.mainloop()