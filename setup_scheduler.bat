@echo off
chcp 65001 >nul
echo ============================================
echo   GSC 自动报告 v4 - 定时任务安装
echo ============================================
echo.
echo   日报: 每天 09:00 (北京时间)
echo   周报: 每周日 12:00 (北京时间)
echo   月报: 每月最后一天 09:00 (北京时间)
echo.
echo   前提: 系统时区 = UTC+8 (中国标准时间)
echo ============================================
echo.

set SCRIPT_DIR=%~dp0
set PYTHON_PATH=python

%PYTHON_PATH% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请确认已安装并加入 PATH
    pause
    exit /b 1
)

echo 项目路径: %SCRIPT_DIR%
echo.

:: ── 日报: 每天 09:00 ──
@REM echo [1/3] 创建日报任务 (每天 09:00)...
@REM schtasks /create /tn "GSC_Daily_Report_v4" ^
@REM     /tr "\"%PYTHON_PATH%\" \"%SCRIPT_DIR%main.py\" --type daily" ^
@REM     /sc daily ^
@REM     /st 09:00 ^
@REM     /f
@REM if %errorlevel% equ 0 (echo       [OK]) else (echo       [FAIL])

:: ── 周报: 每周日 12:00 ──
echo [2/3] 创建周报任务 (每周日 12:00)...
schtasks /create /tn "GSC_Weekly_Report_v4" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_DIR%main.py\" --type weekly" ^
    /sc weekly ^
    /d SUN ^
    /st 12:00 ^
    /f
if %errorlevel% equ 0 (echo       [OK]) else (echo       [FAIL])

:: ── 月报: 每月最后一天 09:00 ──
echo [3/3] 创建月报任务 (每月最后一天 09:00)...
schtasks /create /tn "GSC_Monthly_Report_v4" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_DIR%main.py\" --type monthly" ^
    /sc monthly ^
    /mo lastday ^
    /st 09:00 ^
    /f
if %errorlevel% equ 0 (echo       [OK]) else (echo       [FAIL])

echo.
echo ============================================
echo   安装完成！
echo.
echo   查看任务: schtasks /query /tn "GSC_*"
echo   删除旧版: schtasks /delete /tn "GSC_Daily_Report" /f
echo.
echo   先手动测试: python main.py --type daily
echo ============================================
pause
