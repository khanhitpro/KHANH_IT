@echo off
chcp 65001 >nul
title KHÁNH IT - AI IMAGE CREATOR V3.2
cd /d "%~dp0"

echo.
echo KHÁNH IT - AI IMAGE CREATOR V3.2
echo Đang kiểm tra thư viện...
echo.

python -c "import customtkinter, PIL, openai" >nul 2>&1
if errorlevel 1 (
    echo Đang cài thư viện còn thiếu...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [LỖI] Không cài được thư viện.
        pause
        exit /b 1
    )
)

echo Đang mở phần mềm...
python main.py

if errorlevel 1 (
    echo.
    echo Phần mềm gặp lỗi. Hãy chụp hoặc copy lỗi phía trên gửi lại.
    pause
)
