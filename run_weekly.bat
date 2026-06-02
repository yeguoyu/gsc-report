@echo off
cd /d "%~dp0"

set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897

if not exist logs mkdir logs

python main.py --type weekly >> logs\weekly.log 2>&1