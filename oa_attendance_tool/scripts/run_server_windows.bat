@echo off
REM Windows 服务端快速启动（开发调试）
cd /d %~dp0\..\server
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env
  echo 已生成 .env，请先填写 TD_OA_API_USERNAME / TD_OA_API_PASSWORD（或 APP_ID/APP_SECRET）后再启动。
  pause
)
uvicorn app.main:app --host 127.0.0.1 --port 8848
