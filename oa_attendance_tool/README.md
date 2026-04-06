# 通达OA考勤自动提醒与打卡统计工具（C/S高安全版）

> 新手建议先看：`oa_attendance_tool/USAGE_GUIDE.md`（按“服务器端/客户端”分好并给出Windows启动步骤）。

## 0. 你最关心：OA接口参数到底填哪里（Windows服务端/客户端）

> 结论先说：**只填服务端，不填客户端**。

### 0.1 服务端（Windows，必须填写）
1. 打开 `oa_attendance_tool/server/.env`（可先复制 `.env.example`）。
2. 只在这里填写（V12.9优先用接口用户）：
   - `TD_OA_BASE_URL`
   - `TD_OA_API_USERNAME`
   - `TD_OA_API_PASSWORD`
   - （可选）`TD_OA_APP_ID` / `TD_OA_APP_SECRET`
3. 如果你们通达OA版本接口路径不同，再修改 `oa_attendance_tool/server/app/oa_client.py` 内的 path。

### 0.2 客户端（Windows，禁止填写OA密钥）
- 客户端只填写**服务端地址**（例如 `https://10.10.10.8:8848`）+ 行政账号密码。
- 客户端**不能**也**不需要**填写 `AppID/AppSecret/Token`。

### 0.3 Windows快速启动
- 服务端调试启动：`oa_attendance_tool/scripts/run_server_windows.bat`
- 客户端调试启动：`oa_attendance_tool/scripts/run_client_windows.bat`


### 0.4 你截图这个页面（V12.9 接口管理）要怎么填
你截图是“接口用户信息”页面，对应服务端 `.env` 里的：
- 用户名 -> `TD_OA_API_USERNAME`
- 密码 -> `TD_OA_API_PASSWORD`

你当前要求是“只有读取权限”，建议在 OA 接口管理里：
- ✅ 仅开通读取考勤/人员/分组所需的接口权限
- ❌ 不开通任何写入、审批、修改、删除类权限
- ✅ 保留 token 获取与只读查询接口权限

如果你们OA管理员给的是开放平台应用凭证，再填：`TD_OA_APP_ID / TD_OA_APP_SECRET`。

---

本项目严格遵守以下安全红线：
1. **服务端+客户端完全分离**，OA接口调用与核心计算仅在服务端。
2. **服务端部署于OA内网同安全域**，默认仅监听内网地址。
3. **客户端只访问服务端加密接口**，不持有OA鉴权信息。
4. **职责隔离**，防止鉴权泄露与越权调用。

---

## 1. 需求规格说明书

### 1.1 业务流程
1. 服务端定时从通达OA官方API同步：人员、打卡记录、分组规则。
2. 服务端执行异常规则引擎（迟到/早退/缺卡）。
3. 服务端生成提醒事件并存储，向客户端推送（可扩展企业微信/钉钉/邮件）。
4. 客户端登录服务端后查询统计、处理异常、导出报表。

### 1.2 C/S架构设计
- **Server（内网）**：FastAPI + 调度器 + DB + OA适配层。
- **Client（行政电脑）**：PySide6桌面程序，只做展示与操作下发。

### 1.3 两端职责划分
- **服务端职责（100%核心）**
  - OA鉴权生命周期管理（token获取/刷新/重试）。
  - OA数据同步、缓存、计算、审计日志。
  - 提醒规则存储与执行。
- **客户端职责（0%OA调用）**
  - 登录、查询、展示、导出、提醒接收。
  - 提交规则配置到服务端，不做规则计算。

### 1.4 安全隔离方案
- 仅服务端接触 AppID/AppSecret。
- 客户端双重认证：账号密码 + 设备指纹。
- 服务端IP白名单限制客户端来源。
- TLS 1.3 + 业务层AES二次加密（预留）。
- 敏感字段（联系方式）加密入库。

### 1.5 内网部署拓扑
- OA服务器（同机或同内网）部署 `server`。
- 行政终端安装 `client.exe`。
- 防火墙仅开放服务端内网端口给白名单终端。

### 1.6 功能模块拆解
- 服务端：接口鉴权、同步调度、规则引擎、告警中心、统计查询、审计日志。
- 客户端：连接登录、实时提醒、统计查询、导出报表、规则管理、运行监控。

### 1.7 权限设计说明
- 角色示例：`admin`（配置/查询/处理）与 `viewer`（只读）。
- 所有接口通过JWT鉴权，关键动作写审计日志。

---

## 2. 通达OA接口对接专项方案

### 2.1 核心接口清单（仅服务端调用）
> 注意：不同通达OA版本路径可能不同，请以企业实际官方文档为准。

1. 鉴权接口：`POST /api/open/token`
2. 人员接口：`GET /api/open/users`
3. 考勤分组接口：`GET /api/open/attendance/groups`
4. 打卡记录接口：`GET /api/open/attendance/records`

### 2.2 调用流程
1. 服务端启动读取本地密钥。
2. 获取token并缓存，过期前刷新。
3. 定时同步人员/分组/打卡数据。
4. 规则引擎生成异常事件并触发提醒。
5. 客户端仅通过 `/api/query`、`/api/events/handle` 等接口获取/处理数据。

### 2.3 鉴权方案
- OA鉴权：仅服务端维护 `app_id/app_secret`。
- 客户端鉴权：`/api/auth/login` 签发JWT。
- 设备绑定：首次登录写入设备指纹，后续必须匹配。

### 2.4 异常处理方案
- 网络超时：3次指数退避重试（建议）。
- 错误码：落库到 `audit_logs` 并触发告警。
- 空数据：记录INFO日志，避免误判崩溃。
- 数据异常：字段校验失败时丢弃并记录错误。

### 2.5 版本适配注意事项
- V11与V12常见差异在：token返回字段名、时间字段格式（时间戳/ISO字符串）、分页参数。
- 建议在 `oa_client.py` 做“版本适配层”，统一转换为内部数据模型。

---

## 3. 完整可运行项目代码

目录结构：

```text
oa_attendance_tool/
  server/                # 服务端（FastAPI）
    app/
      main.py
      config.py
      database.py
      models.py
      schemas.py
      security.py
      oa_client.py
      rule_engine.py
    requirements.txt
  client/                # 客户端（PySide6）
    main.py
    requirements.txt
  database/
    schema.sql
  docs/
```

快速启动：

```bash
# 服务端
cd oa_attendance_tool/server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8848

# 客户端
cd ../client
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 4. 数据库表结构设计

详见：`database/schema.sql`

- 关键表：`employees`、`attendance_groups`、`attendance_records`、`abnormal_events`、`audit_logs`。
- 索引：按用户+时间、用户+日期、操作+时间建立复合索引。
- 加密：联系方式字段 `contact_encrypted` 采用服务端加密后落库。

---

## 5. 部署与使用手册

### 5.1 服务端部署手册

#### A. 环境搭建
- Linux/Windows Server 安装 Python 3.11+
- 创建虚拟环境并安装依赖。

#### B. 配置文件
在 `server/.env` 填写：
- `TD_OA_BASE_URL`
- `TD_OA_API_USERNAME`
- `TD_OA_API_PASSWORD`
- （可选）`TD_OA_APP_ID` / `TD_OA_APP_SECRET`
- `JWT_SECRET`
- `ALLOWED_CLIENT_IPS`

#### C. 服务注册
- Linux systemd：
  - `ExecStart=/path/to/uvicorn app.main:app --host 10.x.x.x --port 8848`
  - `Restart=always`
- Windows：使用 `nssm` 注册为系统服务，设为自动启动。

#### D. 接口权限申请
- 在通达OA开放平台申请考勤和组织接口权限。
- 开启IP限制，仅允许服务端宿主IP调用OA接口。

#### E. 常见问题排查
- 登录403：检查IP白名单和设备指纹。
- 同步失败：检查OA地址、证书、token接口返回。
- 查询无数据：检查同步任务是否执行、分组ID是否一致。

### 5.2 客户端安装使用手册

1. 使用 `PyInstaller` 打包：
   - `pyinstaller -F -w main.py -n OAAttendanceClient`
2. 分发 `OAAttendanceClient.exe` 到行政电脑。
3. 首次使用：填写服务端地址、账号密码、测试连通、登录。
4. 查询统计：输入分组与日期范围，点击“查询统计”。
5. 导出：点击“导出CSV”。
6. 规则调整：通过客户端调用服务端规则接口提交。

---

## 6. 安全合规说明

- 严禁客户端直连OA：已通过架构与代码隔离。
- OA鉴权仅服务端持有：客户端代码无相关字段。

- 只读权限约束：服务端 OA 适配器默认阻止除 token 之外的非 GET 请求，防止误调用写接口。
- 访问控制：JWT + 设备绑定 + IP白名单。
- 通信安全：建议启用内网TLS 1.3（反向代理或Uvicorn证书）。
- 数据安全：敏感字段加密、日志审计可追溯、最小权限原则。

---

## 7. 测试用例

### 7.1 接口连通性测试
- 用例：客户端请求 `/api/health`
- 预期：返回 `status=ok`

### 7.2 两端通信测试
- 用例：正确账号密码+授权设备登录
- 预期：返回JWT

### 7.3 核心功能测试
- 用例：手动触发 `/api/sync`
- 预期：写入打卡记录并产生异常事件

### 7.4 异常场景测试
- 用例：OA接口超时
- 预期：写入错误日志，不崩溃

### 7.5 权限隔离测试
- 用例：未授权设备登录
- 预期：403拒绝

### 7.6 安全合规测试
- 用例：在客户端检索OA密钥
- 预期：不存在AppSecret/Token等敏感字段

