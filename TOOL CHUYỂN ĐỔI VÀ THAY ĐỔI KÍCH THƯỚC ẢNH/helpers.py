import datetime
import os
import platform

def get_system_info():
    """Hàm lấy thông tin hệ điều hành hiện tại"""
    return f"{platform.system()} {platform.release()} (Phiên bản: {platform.version()})"

def format_current_time():
    """Hàm định dạng thời gian hiện tại"""
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def check_file_exists(file_path):
    """Hàm kiểm tra xem một file tài nguyên có tồn tại hay không"""
    if os.path.exists(file_path):
        return f"✅ Tìm thấy file: {file_path}"
    else:
        return f"❌ Không tìm thấy file: {file_path}"