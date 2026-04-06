# 通达OA考勤工具使用指南（先看这个）

> 目标：让你一眼看懂**哪些是服务器端**、**哪些是客户端**，以及如何在 Windows 上快速跑起来。

## 1) 文件怎么分（你最关心）

### A. 服务器端（部署在 OA 内网服务器）
目录：`oa_attendance_tool/server/`

- `app/main.py`：服务端入口（提供 API、定时同步、异常计算）
- `app/oa_client.py`：通达OA接口适配（只读模式，除 token 外只允许 GET）
- `app/config.py`：服务端配置项定义
- `app/security.py`：JWT、密码、加密工具
- `app/models.py`：数据库模型
- `app/database.py`：数据库连接
- `app/schemas.py`：请求/响应模型
- `.env.example`：服务端配置模板（复制为 `.env` 后填写 OA 参数）
- `requirements.txt`：服务端依赖

### B. 客户端（安装在行政电脑）
目录：`oa_attendance_tool/client/`

- `main.py`：桌面客户端程序（登录服务端、查询、导出）
- `requirements.txt`：客户端依赖

### C. 公共与辅助文件
- `oa_attendance_tool/database/schema.sql`：数据库建表脚本
- `oa_attendance_tool/scripts/run_server_windows.bat`：Windows 启动服务端
- `oa_attendance_tool/scripts/run_client_windows.bat`：Windows 启动客户端
- `oa_attendance_tool/README.md`：完整设计文档（架构、安全、部署、测试）

---

## 2) 你该怎么用（Windows）

## 步骤1：先配服务器端
在 OA 服务器上：

1. 打开 `oa_attendance_tool/server/`
2. 复制配置文件：
   - 把 `.env.example` 复制为 `.env`
3. 编辑 `.env`，至少填写：
   - `TD_OA_BASE_URL`
   - `TD_OA_API_USERNAME`
   - `TD_OA_API_PASSWORD`
   - `JWT_SECRET`
   - `ALLOWED_CLIENT_IPS`

> 注意：OA 凭据只放服务端，客户端不要放。

## 步骤2：启动服务器端
方式一（推荐，最简单）：
- 双击：`oa_attendance_tool/scripts/run_server_windows.bat`

方式二（手工命令）：
```bat
cd oa_attendance_tool\server
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8848
```

## 步骤3：启动客户端
在行政电脑上：

方式一（推荐）：
- 双击：`oa_attendance_tool/scripts/run_client_windows.bat`

方式二（手工命令）：
```bat
cd oa_attendance_tool\client
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py main.py
```

## 步骤4：客户端连接
在客户端界面填写：
- 服务端地址：`https://服务器IP:8848`（或测试期 `http://服务器IP:8848`）
- 行政账号密码（服务端账号）
- 分组和日期

点击顺序建议：
1) 测试连通
2) 登录
3) 查询统计
4) 导出CSV

---

## 3) 快速排错

- 登录失败 401：检查服务端账号密码。
- 登录失败 403：检查 `ALLOWED_CLIENT_IPS` 白名单、设备绑定是否变更。
- 同步失败：检查 OA 地址、接口账号是否只读可查、token 接口是否可用。
- 查询为空：先在服务端执行一次手动同步 `/api/sync`。

---

## 4) 一句话记忆

- `server/` = **服务器端（唯一可接触OA）**
- `client/` = **客户端（只连 server，不连 OA）**

