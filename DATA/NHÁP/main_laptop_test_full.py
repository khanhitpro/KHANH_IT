import os
import json
import time
import socket
import platform
import subprocess
import threading
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import psutil
except ImportError:
    psutil = None

APP_TITLE = "KHÁNH IT - FULL LAPTOP DIAGNOSTIC"
APP_VERSION = "1.0"

BG = "#0b1220"
PANEL = "#111827"
PANEL2 = "#172033"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
ACCENT = "#f97316"
GREEN = "#22c55e"
YELLOW = "#eab308"
RED = "#ef4444"
BLUE = "#38bdf8"


def run_cmd(cmd, timeout=15):
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
            encoding="utf-8",
            errors="ignore",
        )
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return f"Lỗi: {e}"


def ps(script, timeout=15):
    return run_cmd(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout,
    )


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def bytes_gb(n):
    try:
        return round(float(n) / (1024 ** 3), 2)
    except Exception:
        return 0


class ScreenTest(tk.Toplevel):
    COLORS = [
        ("ĐEN", "black"),
        ("TRẮNG", "white"),
        ("ĐỎ", "red"),
        ("XANH LÁ", "lime"),
        ("XANH DƯƠNG", "blue"),
        ("XÁM", "gray"),
        ("VÀNG", "yellow"),
        ("TÍM", "magenta"),
    ]

    def __init__(self, parent, done_cb):
        super().__init__(parent)
        self.done_cb = done_cb
        self.idx = 0
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.finish(False))
        self.bind("<Left>", lambda e: self.prev())
        self.bind("<Right>", lambda e: self.next())
        self.bind("<space>", lambda e: self.next())
        self.bind("<Return>", lambda e: self.finish(True))
        self.label = tk.Label(self, font=("Segoe UI", 24, "bold"))
        self.label.pack(expand=True, fill="both")
        self.render()

    def render(self):
        name, color = self.COLORS[self.idx]
        fg = "black" if color in ("white", "lime", "yellow") else "white"
        self.label.configure(
            bg=color,
            fg=fg,
            text=(
                f"{name}\n\n"
                "Quan sát điểm chết / ám màu / sọc màn hình\n"
                "← → hoặc SPACE: đổi màu | ENTER: đạt | ESC: lỗi"
            ),
        )

    def next(self):
        self.idx = (self.idx + 1) % len(self.COLORS)
        self.render()

    def prev(self):
        self.idx = (self.idx - 1) % len(self.COLORS)
        self.render()

    def finish(self, ok):
        self.done_cb(ok)
        self.destroy()


class KeyboardTest(tk.Toplevel):
    KEYS = [
        "ESC","F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
        "`","1","2","3","4","5","6","7","8","9","0","-","=","BACKSPACE",
        "TAB","Q","W","E","R","T","Y","U","I","O","P","[","]","\\",
        "CAPSLOCK","A","S","D","F","G","H","J","K","L",";","'","ENTER",
        "SHIFT_L","Z","X","C","V","B","N","M",",",".","/","SHIFT_R",
        "CTRL_L","WIN","ALT_L","SPACE","ALT_R","CTRL_R",
        "UP","DOWN","LEFT","RIGHT"
    ]

    def __init__(self, parent, done_cb):
        super().__init__(parent)
        self.done_cb = done_cb
        self.title("TEST BÀN PHÍM")
        self.geometry("1050x620")
        self.configure(bg=BG)
        self.pressed = set()

        tk.Label(
            self,
            text="TEST BÀN PHÍM - BẤM TỪNG PHÍM",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=15)

        self.info = tk.Label(
            self, text="", bg=BG, fg=MUTED, font=("Segoe UI", 11)
        )
        self.info.pack()

        self.frame = tk.Frame(self, bg=BG)
        self.frame.pack(expand=True, fill="both", padx=15, pady=15)

        self.buttons = {}
        for i, key in enumerate(self.KEYS):
            b = tk.Label(
                self.frame,
                text=key,
                bg=PANEL2,
                fg=TEXT,
                relief="ridge",
                width=10,
                height=2,
                font=("Segoe UI", 9, "bold"),
            )
            b.grid(row=i // 10, column=i % 10, padx=3, pady=3, sticky="nsew")
            self.buttons[key] = b

        for c in range(10):
            self.frame.grid_columnconfigure(c, weight=1)

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(pady=10)

        tk.Button(
            bottom,
            text="ĐẠT",
            command=lambda: self.finish(True),
            bg=GREEN,
            fg="white",
            width=16,
        ).pack(side="left", padx=8)

        tk.Button(
            bottom,
            text="CÓ PHÍM LỖI",
            command=lambda: self.finish(False),
            bg=RED,
            fg="white",
            width=16,
        ).pack(side="left", padx=8)

        self.bind("<KeyPress>", self.on_key)
        self.focus_force()
        self.update_info()

    def normalize(self, e):
        k = e.keysym.upper()
        mapping = {
            "ESCAPE": "ESC",
            "RETURN": "ENTER",
            "BACKSPACE": "BACKSPACE",
            "TAB": "TAB",
            "CAPS_LOCK": "CAPSLOCK",
            "SHIFT_L": "SHIFT_L",
            "SHIFT_R": "SHIFT_R",
            "CONTROL_L": "CTRL_L",
            "CONTROL_R": "CTRL_R",
            "ALT_L": "ALT_L",
            "ALT_R": "ALT_R",
            "SPACE": "SPACE",
            "UP": "UP",
            "DOWN": "DOWN",
            "LEFT": "LEFT",
            "RIGHT": "RIGHT",
            "SUPER_L": "WIN",
            "WIN_L": "WIN",
        }
        return mapping.get(k, k)

    def on_key(self, e):
        key = self.normalize(e)
        if key in self.buttons:
            self.pressed.add(key)
            self.buttons[key].configure(bg=GREEN)
            self.update_info()

    def update_info(self):
        self.info.configure(
            text=f"Đã nhận: {len(self.pressed)}/{len(self.KEYS)} phím"
        )

    def finish(self, ok):
        self.done_cb(ok, len(self.pressed), len(self.KEYS))
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(1050, 700)
        self.configure(bg=BG)

        self.results = {}
        self.score = 100

        self.build_ui()
        self.after(300, self.load_overview)

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=TEXT,
            rowheight=30,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=PANEL2,
            foreground=TEXT,
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#1f2937")])

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=18, pady=(14, 6))

        tk.Label(
            top,
            text="KHÁNH IT",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left")

        tk.Label(
            top,
            text="  FULL LAPTOP DIAGNOSTIC",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")

        tk.Label(
            top,
            text=f"v{APP_VERSION}",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="right")

        action = tk.Frame(self, bg=BG)
        action.pack(fill="x", padx=18, pady=8)

        tk.Button(
            action,
            text="▶ TEST TOÀN BỘ LAPTOP",
            command=self.start_full_test,
            bg=ACCENT,
            fg="white",
            activebackground="#ea580c",
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            padx=18,
            pady=10,
        ).pack(side="left")

        tk.Button(
            action,
            text="TEST MÀN HÌNH",
            command=self.test_screen,
            bg=PANEL2,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=10,
        ).pack(side="left", padx=6)

        tk.Button(
            action,
            text="TEST BÀN PHÍM",
            command=self.test_keyboard,
            bg=PANEL2,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=10,
        ).pack(side="left", padx=6)

        tk.Button(
            action,
            text="XUẤT BÁO CÁO",
            command=self.export_report,
            bg=PANEL2,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=10,
        ).pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.pack(expand=True, fill="both", padx=18, pady=8)

        left = tk.Frame(body, bg=PANEL, width=340)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self.machine_lbl = tk.Label(
            left,
            text="Đang đọc thông tin máy...",
            justify="left",
            anchor="nw",
            bg=PANEL,
            fg=TEXT,
            font=("Consolas", 10),
            padx=16,
            pady=16,
        )
        self.machine_lbl.pack(fill="x")

        tk.Label(
            left,
            text="ĐIỂM SỨC KHỎE",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=(12, 2))

        self.score_lbl = tk.Label(
            left,
            text="--",
            bg=PANEL,
            fg=GREEN,
            font=("Segoe UI", 42, "bold"),
        )
        self.score_lbl.pack()

        self.conclusion_lbl = tk.Label(
            left,
            text="Chưa kiểm tra",
            bg=PANEL,
            fg=MUTED,
            wraplength=300,
            font=("Segoe UI", 11, "bold"),
        )
        self.conclusion_lbl.pack(pady=(0, 10))

        tk.Label(
            left,
            text="TIẾN TRÌNH",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=(15, 6))

        self.progress = ttk.Progressbar(left, maximum=100)
        self.progress.pack(fill="x", padx=18)

        self.status_lbl = tk.Label(
            left,
            text="Sẵn sàng",
            bg=PANEL,
            fg=BLUE,
            wraplength=300,
            font=("Segoe UI", 10),
        )
        self.status_lbl.pack(padx=15, pady=12)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", expand=True, fill="both")

        columns = ("hangmuc", "thongtin", "trangthai")
        self.tree = ttk.Treeview(right, columns=columns, show="headings")
        self.tree.heading("hangmuc", text="HẠNG MỤC")
        self.tree.heading("thongtin", text="THÔNG TIN / KẾT QUẢ")
        self.tree.heading("trangthai", text="TRẠNG THÁI")
        self.tree.column("hangmuc", width=190, anchor="w")
        self.tree.column("thongtin", width=520, anchor="w")
        self.tree.column("trangthai", width=130, anchor="center")
        self.tree.pack(expand=True, fill="both")

        logbox = tk.Frame(self, bg=BG)
        logbox.pack(fill="x", padx=18, pady=(0, 14))

        self.log = tk.Text(
            logbox,
            height=6,
            bg="#060b14",
            fg="#cbd5e1",
            insertbackground="white",
            relief="flat",
            font=("Consolas", 9),
        )
        self.log.pack(fill="x")

    def ui(self, fn, *args, **kwargs):
        self.after(0, lambda: fn(*args, **kwargs))

    def add_result(self, key, info, status="OK", penalty=0):
        self.results[key] = {
            "info": str(info),
            "status": status,
            "penalty": penalty,
        }

        if penalty:
            self.score = max(0, self.score - penalty)

        icon = (
            "✅ TỐT"
            if status == "OK"
            else ("⚠ CẢNH BÁO" if status == "WARN" else "❌ LỖI")
        )

        self.ui(self.refresh_tree)
        self.ui(self.update_score)
        self.ui(self.write_log, f"{key}: {info} [{icon}]")

    def refresh_tree(self):
        for x in self.tree.get_children():
            self.tree.delete(x)

        for k, v in self.results.items():
            icon = (
                "✅ TỐT"
                if v["status"] == "OK"
                else ("⚠ CẢNH BÁO" if v["status"] == "WARN" else "❌ LỖI")
            )
            self.tree.insert("", "end", values=(k, v["info"], icon))

    def update_score(self):
        color = GREEN if self.score >= 85 else YELLOW if self.score >= 65 else RED
        self.score_lbl.configure(text=f"{self.score}/100", fg=color)

        if not self.results:
            text = "Chưa kiểm tra"
        elif self.score >= 90:
            text = "LAPTOP HOẠT ĐỘNG RẤT TỐT"
        elif self.score >= 80:
            text = "LAPTOP HOẠT ĐỘNG TỐT"
        elif self.score >= 65:
            text = "CẦN KIỂM TRA MỘT SỐ HẠNG MỤC"
        else:
            text = "PHÁT HIỆN NHIỀU VẤN ĐỀ"

        self.conclusion_lbl.configure(text=text)

    def write_log(self, text):
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log.see("end")

    def load_overview(self):
        def worker():
            model = ps("(Get-CimInstance Win32_ComputerSystem).Model")
            maker = ps("(Get-CimInstance Win32_ComputerSystem).Manufacturer")
            serial = ps("(Get-CimInstance Win32_BIOS).SerialNumber")
            bios = ps("(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion")

            text = (
                f"Hãng      : {maker}\n"
                f"Model     : {model}\n"
                f"Serial    : {serial}\n"
                f"Windows   : {platform.platform()}\n"
                f"BIOS      : {bios}\n"
                f"Tên máy   : {platform.node()}"
            )
            self.ui(self.machine_lbl.configure, text=text)

        threading.Thread(target=worker, daemon=True).start()

    def start_full_test(self):
        self.results.clear()
        self.score = 100
        self.refresh_tree()
        self.update_score()
        self.progress["value"] = 0
        self.log.delete("1.0", "end")

        threading.Thread(target=self.full_test_worker, daemon=True).start()

    def progress_step(self, value, text):
        self.ui(self.progress.configure, value=value)
        self.ui(self.status_lbl.configure, text=text)

    def full_test_worker(self):
        tests = [
            ("CPU", self.test_cpu),
            ("RAM", self.test_ram),
            ("Ổ CỨNG", self.test_disk),
            ("GPU", self.test_gpu),
            ("PIN", self.test_battery),
            ("MAINBOARD / BIOS", self.test_board),
            ("MÀN HÌNH", self.test_display_info),
            ("WIFI / MẠNG", self.test_network),
            ("BLUETOOTH", self.test_bluetooth),
            ("WEBCAM", self.test_webcam_device),
            ("ÂM THANH", self.test_audio_device),
            ("USB", self.test_usb),
            ("WINDOWS", self.test_windows),
            ("HIỆU NĂNG NHANH", self.quick_benchmark),
        ]

        total = len(tests)

        for i, (name, fn) in enumerate(tests, 1):
            self.progress_step(
                int((i - 1) / total * 100),
                f"Đang kiểm tra: {name}",
            )

            try:
                fn()
            except Exception as e:
                self.add_result(
                    name,
                    f"Không thể kiểm tra: {e}",
                    "WARN",
                    2,
                )

            self.progress_step(
                int(i / total * 100),
                f"Đã kiểm tra: {name}",
            )

        self.ui(
            self.status_lbl.configure,
            text="Hoàn tất test tự động. Hãy test thêm màn hình và bàn phím.",
        )

        self.ui(
            messagebox.showinfo,
            "Hoàn tất",
            "Đã hoàn tất phần kiểm tra tự động.\n\n"
            "Để kiểm tra vật lý chính xác hơn, hãy chạy thêm "
            "TEST MÀN HÌNH và TEST BÀN PHÍM.",
        )

    def test_cpu(self):
        name = ps("(Get-CimInstance Win32_Processor).Name")
        cores = os.cpu_count() or 0
        usage = psutil.cpu_percent(interval=1) if psutil else 0

        freq = ""
        if psutil:
            f = psutil.cpu_freq()
            if f:
                freq = f" | {round(f.current)} MHz"

        self.add_result(
            "CPU",
            f"{name} | {cores} luồng | tải {usage}%{freq}",
        )

    def test_ram(self):
        if psutil:
            vm = psutil.virtual_memory()
            total = bytes_gb(vm.total)
            usage = vm.percent
        else:
            total = safe_float(
                ps(
                    "[math]::Round("
                    "(Get-CimInstance Win32_ComputerSystem)."
                    "TotalPhysicalMemory/1GB,2)"
                )
            )
            usage = 0

        sticks = ps(
            "(Get-CimInstance Win32_PhysicalMemory | Measure-Object).Count"
        )

        speed = ps(
            "(Get-CimInstance Win32_PhysicalMemory | "
            "Select-Object -ExpandProperty Speed | "
            "Sort-Object -Unique) -join '/'"
        )

        status = "WARN" if usage >= 90 else "OK"

        self.add_result(
            "RAM",
            f"{total} GB | {sticks} thanh | {speed} MHz | đang dùng {usage}%",
            status,
            4 if status == "WARN" else 0,
        )

    def test_disk(self):
        script = '''
$items = Get-PhysicalDisk | ForEach-Object {
    [PSCustomObject]@{
        FriendlyName=$_.FriendlyName
        MediaType=$_.MediaType
        SizeGB=[math]::Round($_.Size/1GB,0)
        HealthStatus=$_.HealthStatus
        OperationalStatus=($_.OperationalStatus -join ",")
    }
}
$items | ConvertTo-Json -Compress
'''
        raw = ps(script)

        try:
            data = json.loads(raw)

            if isinstance(data, dict):
                data = [data]

            infos = []
            bad = False

            for d in data:
                health = d.get("HealthStatus", "Unknown")

                if health not in ("Healthy", "Unknown"):
                    bad = True

                infos.append(
                    f"{d.get('FriendlyName')} "
                    f"{d.get('SizeGB')}GB "
                    f"{d.get('MediaType')} - {health}"
                )

            self.add_result(
                "SSD / HDD",
                " | ".join(infos),
                "WARN" if bad else "OK",
                10 if bad else 0,
            )

        except Exception:
            drives = ps(
                "(Get-CimInstance Win32_DiskDrive | ForEach-Object { "
                "$_.Model + ' ' + "
                "[math]::Round($_.Size/1GB,0) + 'GB' }) -join ' | '"
            )

            self.add_result(
                "SSD / HDD",
                drives or "Không đọc được SMART/PhysicalDisk",
                "WARN" if not drives else "OK",
                3 if not drives else 0,
            )

    def test_gpu(self):
        gpu = ps(
            "(Get-CimInstance Win32_VideoController | ForEach-Object { "
            "$_.Name + ' (' + $_.DriverVersion + ')' }) -join ' | '"
        )

        self.add_result(
            "GPU",
            gpu or "Không phát hiện GPU",
            "OK" if gpu else "WARN",
            5 if not gpu else 0,
        )

    def test_battery(self):
        battery = psutil.sensors_battery() if psutil else None

        design = ps(
            "(Get-CimInstance -Namespace root/wmi "
            "-ClassName BatteryStaticData "
            "-ErrorAction SilentlyContinue).DesignedCapacity"
        )

        full = ps(
            "(Get-CimInstance -Namespace root/wmi "
            "-ClassName BatteryFullChargedCapacity "
            "-ErrorAction SilentlyContinue).FullChargedCapacity"
        )

        design_value = safe_float(design)
        full_value = safe_float(full)

        health = (
            round(full_value / design_value * 100, 1)
            if design_value > 0 and full_value > 0
            else None
        )

        percent = round(battery.percent, 1) if battery else None

        if health is not None:
            wear = round(100 - health, 1)

            if health >= 80:
                status = "OK"
                penalty = 0
            elif health >= 60:
                status = "WARN"
                penalty = 8
            else:
                status = "FAIL"
                penalty = 15

            self.add_result(
                "PIN",
                f"Pin hiện tại {percent if percent is not None else '?'}% | "
                f"Health {health}% | Chai {wear}%",
                status,
                penalty,
            )

        elif battery:
            self.add_result(
                "PIN",
                f"Pin hiện tại {percent}%. "
                "Không đọc được Design/Full Charge Capacity.",
                "WARN",
                2,
            )

        else:
            self.add_result(
                "PIN",
                "Không phát hiện pin hoặc máy bàn",
                "WARN",
                1,
            )

    def test_board(self):
        board = ps(
            "(Get-CimInstance Win32_BaseBoard | ForEach-Object { "
            "$_.Manufacturer + ' ' + $_.Product }) -join ' | '"
        )

        bios = ps(
            "(Get-CimInstance Win32_BIOS | ForEach-Object { "
            "$_.SMBIOSBIOSVersion }) -join ' | '"
        )

        self.add_result(
            "MAINBOARD / BIOS",
            f"{board} | BIOS {bios}",
        )

    def test_display_info(self):
        info = ps(
            "(Get-CimInstance Win32_VideoController | ForEach-Object { "
            "$_.CurrentHorizontalResolution.ToString() + 'x' + "
            "$_.CurrentVerticalResolution.ToString() + ' @ ' + "
            "$_.CurrentRefreshRate.ToString() + 'Hz' }) -join ' | '"
        )

        self.add_result(
            "MÀN HÌNH",
            info or "Không đọc được độ phân giải/tần số",
            "OK" if info else "WARN",
            2 if not info else 0,
        )

    def test_network(self):
        adapters = ps(
            "(Get-NetAdapter -ErrorAction SilentlyContinue | "
            "Where-Object {$_.Status -eq 'Up'} | ForEach-Object { "
            "$_.Name + ': ' + $_.LinkSpeed }) -join ' | '"
        )

        internet = False

        try:
            s = socket.create_connection(("1.1.1.1", 53), timeout=2)
            s.close()
            internet = True
        except Exception:
            pass

        status = "OK" if adapters else "WARN"

        self.add_result(
            "WIFI / MẠNG",
            f"{adapters or 'Không có adapter đang kết nối'} | "
            f"Internet: {'Có' if internet else 'Không'}",
            status,
            3 if status == "WARN" else 0,
        )

    def test_bluetooth(self):
        bt = ps(
            "(Get-PnpDevice -Class Bluetooth -Status OK "
            "-ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty FriendlyName) -join ' | '"
        )

        self.add_result(
            "BLUETOOTH",
            bt or "Không phát hiện thiết bị Bluetooth đang hoạt động",
            "OK" if bt else "WARN",
            2 if not bt else 0,
        )

    def test_webcam_device(self):
        cam = ps(
            "(Get-PnpDevice -Class Camera -Status OK "
            "-ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty FriendlyName) -join ' | '"
        )

        if not cam:
            cam = ps(
                "(Get-PnpDevice -Class Image -Status OK "
                "-ErrorAction SilentlyContinue | "
                "Where-Object {$_.FriendlyName -match 'camera|webcam'} | "
                "Select-Object -ExpandProperty FriendlyName) -join ' | '"
            )

        self.add_result(
            "WEBCAM",
            cam or "Không phát hiện webcam",
            "OK" if cam else "WARN",
            3 if not cam else 0,
        )

    def test_audio_device(self):
        audio = ps(
            "(Get-PnpDevice -Class Media -Status OK "
            "-ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty FriendlyName) -join ' | '"
        )

        self.add_result(
            "ÂM THANH",
            audio or "Không phát hiện thiết bị âm thanh",
            "OK" if audio else "WARN",
            4 if not audio else 0,
        )

    def test_usb(self):
        count = ps(
            "(Get-PnpDevice -Class USB -Status OK "
            "-ErrorAction SilentlyContinue | Measure-Object).Count"
        )

        c = int(safe_float(count))

        self.add_result(
            "USB",
            f"Windows nhận {c} thiết bị/controller USB",
            "OK" if c else "WARN",
            2 if not c else 0,
        )

    def test_windows(self):
        version = platform.platform()

        status_value = ps(
            "(Get-CimInstance SoftwareLicensingProduct | "
            "Where-Object {$_.PartialProductKey -and "
            "$_.Name -like 'Windows*'} | "
            "Select-Object -First 1 -ExpandProperty LicenseStatus)"
        )

        activated = str(status_value).strip() == "1"

        self.add_result(
            "WINDOWS",
            f"{version} | Kích hoạt: "
            f"{'Có' if activated else 'Chưa xác định/Chưa kích hoạt'}",
            "OK" if activated else "WARN",
            2 if not activated else 0,
        )

    def quick_benchmark(self):
        start = time.perf_counter()
        x = 0

        for i in range(1_200_000):
            x = (x + i * i) % 10000019

        cpu_seconds = time.perf_counter() - start

        temp_path = os.path.join(
            tempfile.gettempdir(),
            "khanhit_laptop_test.bin",
        )

        block = os.urandom(1024 * 1024)
        size_mb = 32

        w0 = time.perf_counter()

        with open(temp_path, "wb") as f:
            for _ in range(size_mb):
                f.write(block)

            f.flush()
            os.fsync(f.fileno())

        write_seconds = max(time.perf_counter() - w0, 0.001)

        r0 = time.perf_counter()

        with open(temp_path, "rb") as f:
            while f.read(1024 * 1024):
                pass

        read_seconds = max(time.perf_counter() - r0, 0.001)

        try:
            os.remove(temp_path)
        except Exception:
            pass

        write_speed = round(size_mb / write_seconds, 1)
        read_speed = round(size_mb / read_seconds, 1)

        self.add_result(
            "HIỆU NĂNG NHANH",
            f"CPU test {cpu_seconds:.2f}s | "
            f"Disk ghi ~{write_speed} MB/s | "
            f"đọc ~{read_speed} MB/s",
        )

    def test_screen(self):
        ScreenTest(self, self.screen_done)

    def screen_done(self, ok):
        self.add_result(
            "TEST ĐIỂM CHẾT MÀN HÌNH",
            (
                "Người dùng xác nhận màn hình bình thường"
                if ok
                else "Phát hiện điểm chết/ám màu/sọc hoặc bất thường"
            ),
            "OK" if ok else "FAIL",
            0 if ok else 12,
        )

    def test_keyboard(self):
        KeyboardTest(self, self.keyboard_done)

    def keyboard_done(self, ok, pressed, total):
        self.add_result(
            "TEST BÀN PHÍM",
            f"Đã nhận {pressed}/{total} phím trong bài test",
            "OK" if ok else "FAIL",
            0 if ok else 10,
        )

    def export_report(self):
        if not self.results:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Hãy chạy TEST TOÀN BỘ LAPTOP trước.",
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            initialfile=f"BAO_CAO_TEST_LAPTOP_{platform.node()}.txt",
        )

        if not path:
            return

        lines = [
            "=" * 72,
            "                 KHÁNH IT - BÁO CÁO TEST LAPTOP",
            "=" * 72,
            f"Thời gian: {time.strftime('%d/%m/%Y %H:%M:%S')}",
            f"Tên máy  : {platform.node()}",
            f"Hệ điều hành: {platform.platform()}",
            f"Điểm sức khỏe: {self.score}/100",
            "",
        ]

        for key, value in self.results.items():
            state = (
                "TỐT"
                if value["status"] == "OK"
                else "CẢNH BÁO"
                if value["status"] == "WARN"
                else "LỖI"
            )

            lines.extend(
                [
                    f"[{state}] {key}",
                    f"    {value['info']}",
                    "",
                ]
            )

        lines.extend(
            [
                "=" * 72,
                self.conclusion_lbl.cget("text"),
                "=" * 72,
            ]
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        messagebox.showinfo(
            "Đã xuất",
            f"Đã lưu báo cáo:\n{path}",
        )


if __name__ == "__main__":
    App().mainloop()
