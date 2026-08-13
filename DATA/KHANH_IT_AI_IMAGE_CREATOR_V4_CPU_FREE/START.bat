@echo off
chcp 65001 >nul
title KHANH IT - AI IMAGE CREATOR V4 CPU
cd /d "%~dp0"

echo.
echo ================================================
echo   KHANH IT - AI IMAGE CREATOR V4 CPU - FREE
echo ================================================
echo.
echo Dang kiem tra thu vien...

python -c "import customtkinter, PIL, torch, diffusers, transformers, accelerate" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Lan dau su dung - dang cai thu vien AI.
    echo Qua trinh nay co the mat mot luc...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [LOI] Khong cai duoc thu vien.
        echo Hay copy loi phia tren gui lai.
        pause
        exit /b 1
    )
)

echo.
echo Dang mo phan mem...
python main.py

if errorlevel 1 (
    echo.
    echo [LOI] Phan mem da dung.
    echo Hay copy loi phia tren gui lai.
    pause
)
