import os
import subprocess
import sys

def build():
    print("====================================================================")
    print(" 🚀 Bắt đầu đóng gói bảo mật bằng PyArmor (Cú pháp mới) + Spec...")
    print("====================================================================")
    
    # SỬA TẠI ĐÂY: Sử dụng --pack=PhanMem.spec (có dấu =) để PyArmor 9.x nhận diện đúng
    full_command = f'"{sys.executable}" -m pyarmor.cli gen --pack=PhanMem.spec main.py'
    
    try:
        process = subprocess.Popen(full_command, shell=True)
        process.communicate()
        
        if process.returncode == 0:
            print("\n====================================================================")
            print(" 🎉 HOÀN THÀNH XUẤT SẮC!")
            print(" 📂 File EXE bảo mật đã nằm tại thư mục: dist/ ")
            print("====================================================================")
        else:
            print(f"\n ❌ Quá trình build thất bại. Mã lỗi: {process.returncode}")
    except Exception as e:
        print(f"\n ❌ Lỗi hệ thống: {e}")

if __name__ == "__main__":
    build()