@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================
echo  芯讯 - Windows 打包脚本（请在 Windows 上运行）
echo ============================================================

echo [1/3] 准备虚拟环境与依赖...
if not exist .venv (
    py -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install PySide6 pyinstaller || goto :err

echo [2/3] PyInstaller 打包（onedir，启动更快）...
pyinstaller --noconfirm --clean --windowed --onedir ^
    --name ChipNews --icon icon.ico ^
    app.py || goto :err

echo [3/3] 完成。
echo   可直接运行: dist\ChipNews\ChipNews.exe
echo.
echo  生成安装包（需先装 Inno Setup: https://jrsoftware.org/isdl.php）：
echo    iscc installer.iss
echo  生成的安装包在 installer_output\ 下。
echo ============================================================
pause
exit /b 0

:err
echo.
echo [出错] 上一步失败，请检查上面的报错信息。
pause
exit /b 1
