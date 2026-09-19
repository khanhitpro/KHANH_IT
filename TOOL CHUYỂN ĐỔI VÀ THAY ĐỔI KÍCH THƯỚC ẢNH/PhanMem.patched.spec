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


# Pyarmor patch start:

def apply_pyarmor_patch():

    srcpath = ['G:\\KHANH IT GITHUB\\KHANH_IT\\TOOL CHUYỂN ĐỔI VÀ THAY ĐỔI KÍCH THƯỚC ẢNH']
    obfpath = 'G:\\KHANH IT GITHUB\\KHANH_IT\\TOOL CHUYỂN ĐỔI VÀ THAY ĐỔI KÍCH THƯỚC ẢNH\\.pyarmor\\pack\\dist'
    pkgname = 'pyarmor_runtime_000000'
    pkgpath = os.path.join(obfpath, pkgname)
    extpath = os.path.join(pkgname, 'pyarmor_runtime.pyd')

    if hasattr(a.pure, '_code_cache'):
        code_cache = a.pure._code_cache
    else:
        from PyInstaller.config import CONF
        code_cache = CONF['code_cache'].get(id(a.pure))

    srclist = [os.path.normcase(x) for x in srcpath]
    def match_obfuscated_script(orgpath):
        for x in srclist:
            if os.path.normcase(orgpath).startswith(x):
                return os.path.join(obfpath, orgpath[len(x)+1:])

    count = 0
    for i in range(len(a.scripts)):
        x = match_obfuscated_script(a.scripts[i][1])
        if x and os.path.exists(x):
            a.scripts[i] = a.scripts[i][0], x, a.scripts[i][2]
            count += 1
    if count == 0:
        raise RuntimeError('No obfuscated script found')

    for i in range(len(a.pure)):
        x = match_obfuscated_script(a.pure[i][1])
        if x and os.path.exists(x):
            code_cache.pop(a.pure[i][0], None)
            a.pure[i] = a.pure[i][0], x, a.pure[i][2]

    a.pure.append((pkgname, os.path.join(pkgpath, '__init__.py'), 'PYMODULE'))
    a.binaries.append((extpath, os.path.join(obfpath, extpath), 'EXTENSION'))

apply_pyarmor_patch()

# Pyarmor patch end.
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