"""服务端配置模块。

说明：
1. 所有通达OA鉴权参数仅在服务端读取。
2. 支持通过环境变量覆盖，避免硬编码敏感信息。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TD-OA Attendance Secure Server"
    host: str = "127.0.0.1"
    port: int = 8848
    database_url: str = "sqlite:///./attendance.db"

    # 服务端 API 鉴权密钥（客户端只拿到 JWT，不拿到 OA 鉴权）
    jwt_secret: str = "CHANGE_ME_SERVER_JWT_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # 通达 OA 官方接口配置（仅服务端可读）
    td_oa_base_url: str = "http://127.0.0.1:8080"

    # 方案A：开放平台 AppID/AppSecret（部分版本/场景）
    td_oa_app_id: str = ""
    td_oa_app_secret: str = ""

    # 方案B：接口管理里的“接口用户信息”（你截图的12.9界面）
    td_oa_api_username: str = ""
    td_oa_api_password: str = ""

    # V12.9接口路径建议改为可配置，避免写死
    td_oa_token_endpoint: str = "/api/open/token"
    td_oa_users_endpoint: str = "/api/open/users"
    td_oa_groups_endpoint: str = "/api/open/attendance/groups"
    td_oa_records_endpoint: str = "/api/open/attendance/records"

    # 设备绑定 + IP 白名单
    allowed_client_ips: str = "127.0.0.1"

    # AES 二次加密密钥（Base64/Hex 需自行管理）
    transport_aes_key: str = "CHANGE_ME_32_BYTES_KEY_123456789012"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
