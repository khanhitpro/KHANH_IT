# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
project_dir = os.path.abspath(".")

# Tự động quét toàn bộ file tài nguyên (Loại trừ .py và các file hệ thống)
added_files = []
exclude_list = ["build_exe.py", "PhanMem.spec", ".git", "__pycache__", "build", "dist", "logo.ico"]

for root, dirs, files in os.walk(project_dir):
    dirs[:] = [d for d in dirs if d not in exclude_list and not d.startswith('.')]
    for file in files:
        if file.endswith('.py'):
            continue
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, project_dir)
        dest_dir = os.path.dirname(rel_path)
        # Thêm vào danh sách đóng gói (Cú pháp tuple cho PyInstaller)
        added_files.append((rel_path, dest_dir if dest_dir else '.'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files, # Nạp toàn bộ file đã quét vào đây
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='toolchuyendoianh', # Tên file .exe đầu ra
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Đổi thành False nếu muốn ẩn cửa sổ CMD đen khi chạy
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico' if os.path.exists('logo.ico') else None # Nạp logo tự động
)