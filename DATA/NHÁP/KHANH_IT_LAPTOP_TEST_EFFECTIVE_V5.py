import os
import json
import time
import socket
import platform
import subprocess
import threading
import tempfile
import math
import struct
import ctypes
import gc
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import psutil
except ImportError:
    psutil = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    sd = None
    np = None

APP_TITLE = "KHÁNH IT - FULL LAPTOP DIAGNOSTIC"
APP_VERSION = "5.0 EFFECTIVE DIAGNOSTIC"

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
        self.realtime_running = True
        self.net_last = None
        self.net_last_time = None

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
            text="TEST A→Z",
            command=self.start_guided_test,
            bg=GREEN,
            fg="white",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=10,
        ).pack(side="left", padx=6)

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
            action, text="WEBCAM", command=self.test_webcam_live,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=10
        ).pack(side="left", padx=3)

        tk.Button(
            action, text="LOA / MIC", command=self.test_audio_interactive,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=10
        ).pack(side="left", padx=3)

        tk.Button(
            action, text="DASHBOARD", command=self.open_realtime_dashboard,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=10
        ).pack(side="left", padx=3)

        tk.Button(
            action, text="STRESS CPU", command=self.start_cpu_stress,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=10
        ).pack(side="left", padx=3)

        tk.Button(
            action, text="TEST USB", command=self.start_usb_watch,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=10
        ).pack(side="left", padx=3)

        tk.Button(
            action, text="SSD BENCH", command=self.start_disk_benchmark_advanced,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=10
        ).pack(side="left", padx=3)

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
        old_penalty = 0
        if key in self.results:
            old_penalty = int(self.results[key].get("penalty", 0) or 0)

        self.score = min(100, self.score + old_penalty)
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

        fail_count = sum(1 for v in self.results.values() if v.get("status") == "FAIL")
        warn_count = sum(1 for v in self.results.values() if v.get("status") == "WARN")

        if fail_count >= 2:
            text += f" | {fail_count} lỗi nghiêm trọng"
        elif fail_count == 1:
            text += " | Có 1 lỗi cần xử lý"
        elif warn_count >= 4:
            text += f" | {warn_count} cảnh báo"

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
            ("DRIVER", self.test_drivers),
            ("RAM TEST", self.test_ram_memory),
            ("PIN CHI TIẾT", self.test_battery_detail),
            ("SẠC / AC", self.test_ac_power),
            ("TOUCHPAD / CẢM ỨNG", self.test_touch_devices),
            ("WIFI SIGNAL", self.test_wifi_signal),
            ("TỐC ĐỘ MẠNG", self.test_network_speed),
            ("SSD SMART", self.test_smart_extra),
            ("Ổ ĐĨA HỆ THỐNG", self.test_system_disk_space),
            ("LỖI HỆ THỐNG GẦN ĐÂY", self.test_recent_system_errors),
            ("NHIỆT ĐỘ", self.test_temperatures),
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

    def start_guided_test(self):
        self.results.clear()
        self.score = 100
        self.refresh_tree()
        self.update_score()
        self.progress["value"] = 0
        self.log.delete("1.0", "end")

        def worker():
            self.ui(self.status_lbl.configure, text="Bước 1/2: Đang chạy toàn bộ bài test tự động...")
            self.full_test_worker()
            self.ui(self.after, 300, self._guided_physical_tests)

        threading.Thread(target=worker, daemon=True).start()

    def _guided_physical_tests(self):
        messagebox.showinfo(
            "TEST A→Z",
            "Phần test tự động đã xong. Tiếp theo là test vật lý.\n\n"
            "1. Màn hình\n2. Bàn phím\n3. Webcam\n4. Loa / Microphone\n5. USB\n\n"
            "Hãy hoàn tất từng bước để có kết luận chính xác hơn."
        )
        self.test_screen()

    def test_wifi_signal(self):
        raw = run_cmd(["netsh", "wlan", "show", "interfaces"])
        if not raw or "There is no wireless interface" in raw:
            self.add_result("WIFI SIGNAL", "Không phát hiện Wi-Fi hoặc Wi-Fi đang tắt", "WARN", 2)
            return

        signal = None
        ssid = None
        rx = None
        tx = None

        for line in raw.splitlines():
            s = line.strip()
            low = s.lower()
            if low.startswith("signal") and ":" in s:
                try:
                    signal = int(s.split(":", 1)[1].replace("%", "").strip())
                except Exception:
                    pass
            elif low.startswith("ssid") and not low.startswith("bssid") and ":" in s:
                ssid = s.split(":", 1)[1].strip()
            elif "receive rate" in low and ":" in s:
                rx = s.split(":", 1)[1].strip()
            elif "transmit rate" in low and ":" in s:
                tx = s.split(":", 1)[1].strip()

        if signal is None:
            self.add_result("WIFI SIGNAL", "Có Wi-Fi nhưng chưa kết nối mạng không dây", "WARN", 1)
            return

        if signal >= 70:
            st, penalty = "OK", 0
        elif signal >= 45:
            st, penalty = "WARN", 1
        else:
            st, penalty = "WARN", 3

        detail = f"SSID {ssid or '?'} | Signal {signal}%"
        if rx:
            detail += f" | RX {rx} Mbps"
        if tx:
            detail += f" | TX {tx} Mbps"

        self.add_result("WIFI SIGNAL", detail, st, penalty)

    def test_system_disk_space(self):
        try:
            drive = os.environ.get("SystemDrive", "C:") + "\\"
            usage = psutil.disk_usage(drive) if psutil else None
            if usage is None:
                self.add_result("Ổ ĐĨA HỆ THỐNG", "Thiếu psutil", "WARN", 1)
                return

            free_gb = bytes_gb(usage.free)
            total_gb = bytes_gb(usage.total)
            used_pct = usage.percent

            if free_gb < 10:
                st, penalty = "WARN", 4
            elif used_pct >= 90:
                st, penalty = "WARN", 2
            else:
                st, penalty = "OK", 0

            self.add_result(
                "Ổ ĐĨA HỆ THỐNG",
                f"{drive} {total_gb} GB | Trống {free_gb} GB | Đã dùng {used_pct}%",
                st,
                penalty
            )
        except Exception as e:
            self.add_result("Ổ ĐĨA HỆ THỐNG", f"Không kiểm tra được: {e}", "WARN", 1)

    def test_recent_system_errors(self):
        script = """
$start=(Get-Date).AddDays(-7)
$events = Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=$start} -ErrorAction SilentlyContinue |
    Select-Object -First 20 TimeCreated,Id,ProviderName,LevelDisplayName
$events | ConvertTo-Json -Compress
"""
        raw = ps(script, 25)

        if not raw:
            self.add_result("LỖI HỆ THỐNG GẦN ĐÂY", "Không thấy lỗi Critical/Error đáng chú ý trong 7 ngày hoặc không đọc được log", "OK")
            return

        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]

            critical = 0
            errors = 0
            samples = []

            for d in data[:20]:
                level = str(d.get("LevelDisplayName", ""))
                if "Critical" in level:
                    critical += 1
                elif "Error" in level:
                    errors += 1
                samples.append(f"ID {d.get('Id')} {d.get('ProviderName')}")

            if critical > 0:
                st, penalty = "WARN", min(8, 3 + critical)
            elif errors >= 10:
                st, penalty = "WARN", 3
            else:
                st, penalty = "WARN", 1

            self.add_result(
                "LỖI HỆ THỐNG GẦN ĐÂY",
                f"7 ngày: Critical {critical} | Error {errors} | Ví dụ: " + " ; ".join(samples[:4]),
                st,
                penalty
            )
        except Exception:
            self.add_result("LỖI HỆ THỐNG GẦN ĐÂY", "Có lỗi hệ thống gần đây nhưng không phân tích được chi tiết", "WARN", 1)

    def open_realtime_dashboard(self):
        win = tk.Toplevel(self)
        win.title("REALTIME HARDWARE DASHBOARD")
        win.geometry("860x560")
        win.configure(bg=BG)

        tk.Label(
            win, text="REALTIME HARDWARE DASHBOARD",
            bg=BG, fg=TEXT, font=("Segoe UI", 18, "bold")
        ).pack(pady=14)

        grid = tk.Frame(win, bg=BG)
        grid.pack(fill="both", expand=True, padx=20, pady=10)

        cards = {}
        items = ["CPU", "RAM", "PIN", "MẠNG", "Ổ CỨNG", "UPTIME"]
        for i, name in enumerate(items):
            card = tk.Frame(grid, bg=PANEL, bd=0)
            card.grid(row=i//2, column=i%2, sticky="nsew", padx=8, pady=8)
            grid.grid_columnconfigure(i%2, weight=1)
            grid.grid_rowconfigure(i//2, weight=1)

            tk.Label(card, text=name, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 3))
            value = tk.Label(card, text="--", bg=PANEL, fg=TEXT,
                             font=("Segoe UI", 20, "bold"))
            value.pack(anchor="w", padx=14, pady=(0, 4))
            sub = tk.Label(card, text="", bg=PANEL, fg=BLUE,
                           font=("Segoe UI", 9))
            sub.pack(anchor="w", padx=14, pady=(0, 12))
            cards[name] = (value, sub)

        state = {"alive": True, "last_net": psutil.net_io_counters() if psutil else None,
                 "last_t": time.time()}

        def close():
            state["alive"] = False
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", close)

        def update():
            if not state["alive"] or not win.winfo_exists():
                return

            try:
                if psutil:
                    cpu = psutil.cpu_percent(interval=None)
                    freq = psutil.cpu_freq()
                    cards["CPU"][0].configure(text=f"{cpu}%")
                    cards["CPU"][1].configure(
                        text=f"{round(freq.current)} MHz" if freq else ""
                    )

                    vm = psutil.virtual_memory()
                    cards["RAM"][0].configure(text=f"{vm.percent}%")
                    cards["RAM"][1].configure(
                        text=f"{bytes_gb(vm.used)} / {bytes_gb(vm.total)} GB"
                    )

                    b = psutil.sensors_battery()
                    if b:
                        cards["PIN"][0].configure(text=f"{round(b.percent,1)}%")
                        cards["PIN"][1].configure(
                            text="Đang sạc" if b.power_plugged else "Đang dùng pin"
                        )
                    else:
                        cards["PIN"][0].configure(text="N/A")
                        cards["PIN"][1].configure(text="Không phát hiện pin")

                    now = time.time()
                    net = psutil.net_io_counters()
                    dt = max(now - state["last_t"], 0.1)
                    down = (net.bytes_recv - state["last_net"].bytes_recv) / dt / 1024 / 1024
                    up = (net.bytes_sent - state["last_net"].bytes_sent) / dt / 1024 / 1024
                    cards["MẠNG"][0].configure(text=f"↓ {down:.2f} MB/s")
                    cards["MẠNG"][1].configure(text=f"↑ {up:.2f} MB/s")
                    state["last_net"] = net
                    state["last_t"] = now

                    du = psutil.disk_usage(os.environ.get("SystemDrive","C:") + "\\")
                    cards["Ổ CỨNG"][0].configure(text=f"{du.percent}%")
                    cards["Ổ CỨNG"][1].configure(
                        text=f"Còn trống {bytes_gb(du.free)} GB"
                    )

                    uptime = int(time.time() - psutil.boot_time())
                    h = uptime // 3600
                    m = (uptime % 3600) // 60
                    cards["UPTIME"][0].configure(text=f"{h}h {m}m")
                    cards["UPTIME"][1].configure(text="Thời gian máy đã chạy")
            except Exception:
                pass

            win.after(1000, update)

        update()

    def test_ac_power(self):
        try:
            if psutil:
                b = psutil.sensors_battery()
            else:
                b = None

            if b is None:
                self.add_result("SẠC / AC", "Không phát hiện pin; có thể là máy bàn hoặc driver không hỗ trợ", "WARN", 1)
                return

            if b.power_plugged:
                self.add_result("SẠC / AC", f"Đang cắm sạc | Pin {round(b.percent,1)}%", "OK")
            else:
                self.add_result("SẠC / AC", f"Không cắm sạc | Pin {round(b.percent,1)}%", "WARN", 1)
        except Exception as e:
            self.add_result("SẠC / AC", f"Không kiểm tra được trạng thái nguồn: {e}", "WARN", 1)

    def test_touch_devices(self):
        script = """
$items = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | Where-Object {
    $_.FriendlyName -match 'Touchpad|Touch Pad|Precision Touchpad|I2C HID Device|Touch Screen|Touchscreen'
}
$items | ForEach-Object { $_.Class + ': ' + $_.FriendlyName + ' [' + $_.Status + ']' } | Out-String
"""
        raw = ps(script)
        raw = raw.strip().replace("\r\n", " | ").replace("\n", " | ")
        if raw:
            bad = "Error" in raw or "Problem" in raw
            self.add_result("TOUCHPAD / CẢM ỨNG", raw, "WARN" if bad else "OK", 3 if bad else 0)
        else:
            self.add_result("TOUCHPAD / CẢM ỨNG", "Không phát hiện touchpad/màn hình cảm ứng qua PnP", "WARN", 1)

    def test_network_speed(self):
        if psutil is None:
            self.add_result("TỐC ĐỘ MẠNG", "Thiếu psutil", "WARN", 1)
            return
        try:
            before = psutil.net_io_counters()
            t0 = time.time()
            time.sleep(2)
            after = psutil.net_io_counters()
            dt = max(time.time() - t0, 0.1)
            down = (after.bytes_recv - before.bytes_recv) / dt / 1024
            up = (after.bytes_sent - before.bytes_sent) / dt / 1024
            self.add_result(
                "TỐC ĐỘ MẠNG",
                f"Lưu lượng hiện tại ~ Download {down:.1f} KB/s | Upload {up:.1f} KB/s",
                "OK"
            )
        except Exception as e:
            self.add_result("TỐC ĐỘ MẠNG", f"Không đo được lưu lượng mạng: {e}", "WARN", 1)

    def start_disk_benchmark_advanced(self):
        win = tk.Toplevel(self)
        win.title("ADVANCED SSD BENCHMARK")
        win.geometry("560x390")
        win.configure(bg=BG)

        tk.Label(win, text="ADVANCED SSD BENCHMARK", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(pady=18)
        tk.Label(win, text="Benchmark tuần tự với file tạm 128 MB.",
                 bg=BG, fg=MUTED).pack(pady=4)

        result = tk.Label(win, text="Sẵn sàng", bg=BG, fg=BLUE,
                          font=("Segoe UI", 12, "bold"))
        result.pack(pady=16)

        def worker():
            try:
                path = os.path.join(tempfile.gettempdir(), "khanhit_ssd_bench_128.bin")
                size_mb = 128
                block = os.urandom(1024 * 1024)

                t0 = time.perf_counter()
                with open(path, "wb", buffering=0) as f:
                    for _ in range(size_mb):
                        f.write(block)
                w = size_mb / max(time.perf_counter() - t0, 0.001)

                t1 = time.perf_counter()
                with open(path, "rb", buffering=0) as f:
                    while f.read(1024 * 1024):
                        pass
                r = size_mb / max(time.perf_counter() - t1, 0.001)

                try:
                    os.remove(path)
                except Exception:
                    pass

                self.ui(result.configure, text=f"WRITE {w:.1f} MB/s | READ {r:.1f} MB/s")
                self.add_result("SSD BENCHMARK 128MB", f"Ghi {w:.1f} MB/s | Đọc {r:.1f} MB/s", "OK")
            except Exception as e:
                self.ui(result.configure, text=f"Lỗi: {e}")
                self.add_result("SSD BENCHMARK 128MB", f"Lỗi benchmark: {e}", "WARN", 2)

        tk.Button(win, text="BẮT ĐẦU BENCHMARK", bg=ACCENT, fg="white",
                  relief="flat", font=("Segoe UI", 11, "bold"),
                  command=lambda: threading.Thread(target=worker, daemon=True).start(),
                  padx=16, pady=10).pack(pady=15)

    def test_ram_memory(self):
        try:
            if psutil is None:
                self.add_result("RAM TEST", "Thiếu psutil để kiểm tra RAM thực tế", "WARN", 1)
                return

            available = psutil.virtual_memory().available
            test_size = min(256 * 1024 * 1024, max(32 * 1024 * 1024, available // 8))
            block = bytearray(test_size)

            step = 4096
            for i in range(0, test_size, step):
                block[i] = (i // step) % 251

            errors = 0
            for i in range(0, test_size, step):
                if block[i] != (i // step) % 251:
                    errors += 1
                    if errors > 10:
                        break

            del block
            gc.collect()

            mb = round(test_size / (1024 * 1024))
            if errors == 0:
                self.add_result("RAM TEST", f"Đã kiểm tra mẫu {mb} MB | Không phát hiện lỗi đọc/ghi", "OK")
            else:
                self.add_result("RAM TEST", f"Phát hiện {errors} lỗi trong mẫu {mb} MB", "FAIL", 15)
        except Exception as e:
            self.add_result("RAM TEST", f"Lỗi khi test RAM: {e}", "WARN", 2)

    def test_battery_detail(self):
        script = """
$bat = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue
$stat = Get-CimInstance -Namespace root/wmi -ClassName BatteryStaticData -ErrorAction SilentlyContinue
$full = Get-CimInstance -Namespace root/wmi -ClassName BatteryFullChargedCapacity -ErrorAction SilentlyContinue
$cycle = Get-CimInstance -Namespace root/wmi -ClassName BatteryCycleCount -ErrorAction SilentlyContinue
[PSCustomObject]@{
    Name=$bat.Name
    Status=$bat.Status
    EstimatedChargeRemaining=$bat.EstimatedChargeRemaining
    DesignCapacity=$stat.DesignedCapacity
    FullChargeCapacity=$full.FullChargedCapacity
    CycleCount=$cycle.CycleCount
} | ConvertTo-Json -Compress
"""
        raw = ps(script, 20)
        try:
            d = json.loads(raw)
            design = safe_float(d.get("DesignCapacity"))
            full = safe_float(d.get("FullChargeCapacity"))
            cycle = d.get("CycleCount")
            charge = d.get("EstimatedChargeRemaining")
            if design > 0 and full > 0:
                health = round(full / design * 100, 1)
                wear = round(100 - health, 1)
                status = "OK" if health >= 80 else "WARN" if health >= 60 else "FAIL"
                penalty = 0 if status == "OK" else 8 if status == "WARN" else 15
                extra = f" | Cycle {cycle}" if cycle not in (None, "") else ""
                self.add_result(
                    "PIN CHI TIẾT",
                    f"Charge {charge}% | Design {int(design)} mWh | Full {int(full)} mWh | Health {health}% | Chai {wear}%{extra}",
                    status,
                    penalty
                )
            else:
                self.add_result("PIN CHI TIẾT", "Máy/driver không cung cấp đầy đủ dung lượng pin", "WARN", 1)
        except Exception:
            self.add_result("PIN CHI TIẾT", "Không đọc được dữ liệu pin chi tiết", "WARN", 1)

    def start_cpu_stress(self):
        win = tk.Toplevel(self)
        win.title("STRESS TEST CPU")
        win.geometry("560x420")
        win.configure(bg=BG)

        tk.Label(win, text="STRESS TEST CPU", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(pady=18)

        info = tk.Label(win, text="Thời gian: 60 giây", bg=BG, fg=MUTED,
                        font=("Segoe UI", 11))
        info.pack(pady=5)

        prog = ttk.Progressbar(win, maximum=60)
        prog.pack(fill="x", padx=35, pady=15)

        status = tk.Label(win, text="Sẵn sàng", bg=BG, fg=BLUE,
                          font=("Segoe UI", 11, "bold"))
        status.pack(pady=10)

        stop_flag = {"stop": False}

        def worker():
            workers = max(1, min(os.cpu_count() or 2, 8))
            end_time = time.time() + 60

            def burner():
                x = 1
                while time.time() < end_time and not stop_flag["stop"]:
                    x = (x * 13 + 7) % 10000019

            threads = [threading.Thread(target=burner, daemon=True) for _ in range(workers)]
            for t in threads:
                t.start()

            peak = 0
            sec = 0
            while time.time() < end_time and not stop_flag["stop"]:
                time.sleep(1)
                sec += 1
                load = psutil.cpu_percent(interval=None) if psutil else 0
                peak = max(peak, load)
                self.ui(prog.configure, value=sec)
                self.ui(status.configure, text=f"CPU Load: {load}% | Peak: {peak}%")
                self.ui(info.configure, text=f"Còn {max(0,60-sec)} giây")

            stop_flag["stop"] = True
            for t in threads:
                t.join(timeout=1)

            if sec >= 55:
                self.add_result("STRESS CPU", f"Hoàn tất {sec}s | Peak load {peak}%", "OK")
            else:
                self.add_result("STRESS CPU", f"Đã dừng sau {sec}s | Peak load {peak}%", "WARN", 1)

            self.ui(status.configure, text="Đã hoàn tất stress test CPU")

        tk.Button(win, text="BẮT ĐẦU 60 GIÂY",
                  command=lambda: threading.Thread(target=worker, daemon=True).start(),
                  bg=ACCENT, fg="white", relief="flat",
                  font=("Segoe UI", 12, "bold"), width=22, pady=10).pack(pady=15)

        tk.Button(win, text="DỪNG",
                  command=lambda: stop_flag.__setitem__("stop", True),
                  bg=RED, fg="white", relief="flat",
                  font=("Segoe UI", 11, "bold"), width=14, pady=8).pack()

    def start_usb_watch(self):
        win = tk.Toplevel(self)
        win.title("TEST CỔNG USB")
        win.geometry("620x430")
        win.configure(bg=BG)

        tk.Label(win, text="TEST CỔNG USB CẮM / RÚT", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(pady=18)

        tk.Label(win,
                 text="Cắm USB/chuột/thiết bị vào từng cổng. Phần mềm sẽ phát hiện thay đổi thiết bị USB.",
                 bg=BG, fg=MUTED, wraplength=560,
                 font=("Segoe UI", 10)).pack(pady=5)

        box = tk.Text(win, height=12, bg="#060b14", fg="#cbd5e1",
                      relief="flat", font=("Consolas", 9))
        box.pack(fill="both", expand=True, padx=20, pady=15)

        stop = {"v": False}
        detected = {"count": 0}

        def get_usb():
            raw = ps("(Get-PnpDevice -PresentOnly -Class USB -ErrorAction SilentlyContinue | Select-Object -ExpandProperty InstanceId) -join \"`n\"")
            return set(x.strip() for x in raw.splitlines() if x.strip())

        def worker():
            prev = get_usb()
            self.ui(box.insert, "end", f"Ban đầu: {len(prev)} thiết bị/controller USB\n")
            self.ui(box.see, "end")

            while not stop["v"]:
                time.sleep(1)
                cur = get_usb()
                added = cur - prev
                removed = prev - cur
                if added:
                    detected["count"] += len(added)
                    for item in added:
                        self.ui(box.insert, "end", f"[CẮM] {item}\n")
                if removed:
                    for item in removed:
                        self.ui(box.insert, "end", f"[RÚT] {item}\n")
                if added or removed:
                    self.ui(box.see, "end")
                prev = cur

        threading.Thread(target=worker, daemon=True).start()

        def finish():
            stop["v"] = True
            cnt = detected["count"]
            if cnt > 0:
                self.add_result("TEST CỔNG USB", f"Phát hiện {cnt} lần thiết bị USB được cắm", "OK")
            else:
                self.add_result("TEST CỔNG USB", "Chưa phát hiện thiết bị USB mới trong phiên test", "WARN", 1)
            win.destroy()

        tk.Button(win, text="HOÀN TẤT TEST USB", command=finish,
                  bg=GREEN, fg="white", relief="flat",
                  font=("Segoe UI", 11, "bold"), pady=9).pack(pady=(0,15))

    def test_drivers(self):
        bad = ps("(Get-PnpDevice -ErrorAction SilentlyContinue | Where-Object {$_.Status -ne 'OK' -and $_.Status -ne 'Unknown'} | ForEach-Object { $_.Class + ': ' + $_.FriendlyName + ' [' + $_.Status + ']' }) -join ' | '")
        if bad:
            self.add_result("DRIVER", bad, "WARN", 6)
        else:
            self.add_result("DRIVER", "Không phát hiện thiết bị PnP báo lỗi", "OK")

    def test_smart_extra(self):
        script = """
$pd = Get-PhysicalDisk -ErrorAction SilentlyContinue
$out = @()
foreach ($d in $pd) {
    $r = Get-StorageReliabilityCounter -PhysicalDisk $d -ErrorAction SilentlyContinue
    $out += [PSCustomObject]@{
        Name=$d.FriendlyName
        Health=$d.HealthStatus
        Temperature=if($r){$r.Temperature}else{$null}
        PowerOnHours=if($r){$r.PowerOnHours}else{$null}
        Wear=if($r){$r.Wear}else{$null}
        ReadErrors=if($r){$r.ReadErrorsTotal}else{$null}
        WriteErrors=if($r){$r.WriteErrorsTotal}else{$null}
    }
}
$out | ConvertTo-Json -Compress
"""
        raw = ps(script, 25)
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]
            parts, warning = [], False
            for d in data:
                health = d.get("Health")
                temp = d.get("Temperature")
                if health not in ("Healthy", "Unknown", None):
                    warning = True
                if isinstance(temp, (int, float)) and temp >= 60:
                    warning = True
                s = f"{d.get('Name')} | Health {health}"
                if temp is not None: s += f" | {temp}°C"
                if d.get("PowerOnHours") is not None: s += f" | {d.get('PowerOnHours')} giờ"
                if d.get("Wear") is not None: s += f" | Wear {d.get('Wear')}%"
                if d.get("ReadErrors") not in (None, 0):
                    s += f" | ReadErr {d.get('ReadErrors')}"; warning = True
                if d.get("WriteErrors") not in (None, 0):
                    s += f" | WriteErr {d.get('WriteErrors')}"; warning = True
                parts.append(s)
            if parts:
                self.add_result("SSD SMART", " || ".join(parts), "WARN" if warning else "OK", 8 if warning else 0)
            else:
                self.add_result("SSD SMART", "Ổ/driver không cung cấp SMART mở rộng", "WARN", 1)
        except Exception:
            self.add_result("SSD SMART", "Không đọc được SMART mở rộng bằng Windows Storage API", "WARN", 1)

    def test_temperatures(self):
        storage = ps("""
Get-PhysicalDisk -ErrorAction SilentlyContinue | ForEach-Object {
    $r=Get-StorageReliabilityCounter -PhysicalDisk $_ -ErrorAction SilentlyContinue
    if($r -and $r.Temperature){$_.FriendlyName + ': ' + $r.Temperature + '°C'}
}
""")
        if storage:
            self.add_result("NHIỆT ĐỘ", storage.replace("\\r\\n", " | "), "OK")
        else:
            self.add_result("NHIỆT ĐỘ", "Driver không cung cấp cảm biến nhiệt độ trực tiếp", "WARN", 1)

    def test_webcam_live(self):
        if cv2 is None:
            messagebox.showwarning("Thiếu OpenCV", "Cài thư viện: pip install opencv-python")
            return
        def worker():
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.add_result("TEST WEBCAM TRỰC TIẾP", "Không mở được webcam", "FAIL", 6)
                self.ui(messagebox.showerror, "Webcam", "Không mở được webcam.")
                return
            seen = False
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                seen = True
                cv2.putText(frame, "KHANH IT - Q/ESC de thoat", (20,35),
                            cv2.FONT_HERSHEY_SIMPLEX, .7, (255,255,255), 2)
                cv2.imshow("KHANH IT - WEBCAM TEST", frame)
                key = cv2.waitKey(1) & 0xff
                if key in (ord("q"), 27):
                    break
            cap.release()
            cv2.destroyAllWindows()
            self.add_result("TEST WEBCAM TRỰC TIẾP",
                            "Webcam nhận được hình ảnh" if seen else "Không nhận được hình ảnh",
                            "OK" if seen else "FAIL", 0 if seen else 6)
        threading.Thread(target=worker, daemon=True).start()

    def test_audio_interactive(self):
        win = tk.Toplevel(self)
        win.title("TEST LOA / MICROPHONE")
        win.geometry("520x360")
        win.configure(bg=BG)
        tk.Label(win, text="TEST LOA / MICROPHONE", bg=BG, fg=TEXT,
                 font=("Segoe UI",18,"bold")).pack(pady=20)
        tk.Label(win, text="Test loa thực tế và ghi/phát lại microphone 3 giây.",
                 bg=BG, fg=MUTED).pack(pady=5)

        def speaker():
            try:
                import winsound
                winsound.Beep(500,600); winsound.Beep(800,600)
                ok = messagebox.askyesno("Test loa", "Bạn có nghe rõ 2 tiếng beep không?")
                self.add_result("TEST LOA", "Người dùng xác nhận loa hoạt động" if ok else "Loa không nghe rõ/có vấn đề",
                                "OK" if ok else "FAIL", 0 if ok else 7)
            except Exception as e:
                messagebox.showerror("Loa", str(e))

        def mic():
            if sd is None or np is None:
                messagebox.showwarning("Thiếu thư viện", "Cài: pip install sounddevice numpy")
                return
            try:
                rate, duration = 44100, 3
                messagebox.showinfo("Microphone", "Bấm OK rồi nói vào mic trong 3 giây.")
                rec = sd.rec(int(rate*duration), samplerate=rate, channels=1, dtype="float32")
                sd.wait()
                peak = float(np.max(np.abs(rec)))
                sd.play(rec, rate); sd.wait()
                ok = peak > 0.01
                self.add_result("TEST MICROPHONE", f"Mức tín hiệu {peak:.3f}",
                                "OK" if ok else "FAIL", 0 if ok else 6)
            except Exception as e:
                self.add_result("TEST MICROPHONE", f"Lỗi: {e}", "WARN", 2)

        tk.Button(win,text="🔊 TEST LOA",command=speaker,bg=ACCENT,fg="white",
                  relief="flat",font=("Segoe UI",12,"bold"),width=25,pady=10).pack(pady=10)

        def speaker_lr():
            if sd is None or np is None:
                messagebox.showwarning("Thiếu thư viện", "Cài: pip install sounddevice numpy")
                return
            try:
                rate = 44100
                duration = 1.2
                t = np.linspace(0, duration, int(rate*duration), False)
                tone = 0.25*np.sin(2*np.pi*600*t)
                left = np.column_stack((tone, np.zeros_like(tone)))
                right = np.column_stack((np.zeros_like(tone), tone))
                sd.play(left, rate); sd.wait()
                time.sleep(.3)
                sd.play(right, rate); sd.wait()
                ok = messagebox.askyesno("Loa Trái / Phải", "Bạn có nghe lần lượt LOA TRÁI rồi LOA PHẢI không?")
                self.add_result("TEST LOA L/R",
                                "Stereo trái/phải đúng" if ok else "Không xác nhận được stereo trái/phải",
                                "OK" if ok else "FAIL", 0 if ok else 5)
            except Exception as e:
                self.add_result("TEST LOA L/R", f"Lỗi: {e}", "WARN", 2)

        tk.Button(win,text="🔉 TEST LOA TRÁI / PHẢI",command=speaker_lr,bg=PANEL2,fg=TEXT,
                  relief="flat",font=("Segoe UI",11,"bold"),width=25,pady=9).pack(pady=4)
        tk.Button(win,text="🎙 TEST MICROPHONE 3 GIÂY",command=mic,bg=PANEL2,fg=TEXT,
                  relief="flat",font=("Segoe UI",12,"bold"),width=25,pady=10).pack()

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
            f"CPU: {ps('(Get-CimInstance Win32_Processor).Name')}",
            f"RAM: {ps('[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,2)')} GB",
            f"Serial BIOS: {ps('(Get-CimInstance Win32_BIOS).SerialNumber')}",
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

        fail_count = sum(1 for v in self.results.values() if v.get("status") == "FAIL")
        warn_count = sum(1 for v in self.results.values() if v.get("status") == "WARN")
        pass_count = sum(1 for v in self.results.values() if v.get("status") == "OK")

        lines.extend(
            [
                "=" * 72,
                f"TỔNG KẾT: PASS {pass_count} | WARNING {warn_count} | FAIL {fail_count}",
                self.conclusion_lbl.cget("text"),
                "",
                "LƯU Ý: Các bài test phần mềm không thay thế hoàn toàn kiểm tra vật lý.",
                "Nên xác nhận thêm màn hình, bàn phím, touchpad, webcam, loa, mic và từng cổng USB.",
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
