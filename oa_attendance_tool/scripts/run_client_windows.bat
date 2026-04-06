@echo off
REM Windows 客户端快速启动（开发调试）
cd /d %~dp0\..\client
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
py main.py
