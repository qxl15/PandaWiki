"""通达 OA 官方接口客户端（服务端专用）。

说明：
- 这里只提供可运行的示例与接口骨架。
- 实际接口路径、参数签名需按企业所用通达 OA 版本文档调整。
- 已兼容两种鉴权输入：AppID/AppSecret 或 接口用户账号密码（V12.9常见）。
- 默认只允许读取 OA 数据，不允许调用任何写入型 OA 接口。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from .config import settings


class TongdaOAClient:
    """仅在服务端调用，客户端不可见。"""

    def __init__(self) -> None:
        self.base_url = settings.td_oa_base_url.rstrip("/")
        self.app_id = settings.td_oa_app_id
        self.app_secret = settings.td_oa_app_secret
        self.api_username = settings.td_oa_api_username
        self.api_password = settings.td_oa_api_password

        self.token_endpoint = settings.td_oa_token_endpoint
        self.users_endpoint = settings.td_oa_users_endpoint
        self.groups_endpoint = settings.td_oa_groups_endpoint
        self.records_endpoint = settings.td_oa_records_endpoint

        self._token = ""
        self._token_expire_ts = 0

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        # 只读红线：除 token 接口外，所有 OA 调用都必须是 GET。
        m = method.upper()
        if path != self.token_endpoint and m != "GET":
            raise RuntimeError(f"只读模式禁止调用写入型OA接口: {m} {path}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(m, f"{self.base_url}{path}", **kwargs)
            resp.raise_for_status()
            return resp.json()

    async def get_token(self) -> str:
        """获取 OA token。

        优先顺序：
        1) AppID/AppSecret
        2) 接口用户账号密码（你截图的接口管理）
        """
        if self._token:
            return self._token

        payload: dict[str, str]
        if self.app_id and self.app_secret:
            payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        elif self.api_username and self.api_password:
            payload = {"username": self.api_username, "password": self.api_password}
        else:
            raise RuntimeError("未配置 OA 鉴权参数：请在服务端 .env 配置 AppID/AppSecret 或接口用户账号密码")

        data = await self._request("POST", self.token_endpoint, json=payload)

        # 兼容不同字段名
        self._token = (
            data.get("access_token")
            or data.get("token")
            or data.get("data", {}).get("access_token", "")
            or data.get("data", {}).get("token", "")
        )
        if not self._token:
            raise RuntimeError(f"OA鉴权失败，返回内容缺少 token 字段: {data}")
        return self._token

    async def sync_employees(self) -> list[dict[str, Any]]:
        token = await self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        data = await self._request("GET", self.users_endpoint, headers=headers)
        return data.get("items", data.get("data", {}).get("items", []))

    async def sync_groups(self) -> list[dict[str, Any]]:
        token = await self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        data = await self._request("GET", self.groups_endpoint, headers=headers)
        return data.get("items", data.get("data", {}).get("items", []))

    async def sync_records(self, date_from: str, date_to: str) -> list[dict[str, Any]]:
        token = await self.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {"date_from": date_from, "date_to": date_to}
        data = await self._request("GET", self.records_endpoint, headers=headers, params=params)
        return data.get("items", data.get("data", {}).get("items", []))


def to_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")
