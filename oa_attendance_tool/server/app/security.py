"""认证与加密工具。

安全要点：
- OA 鉴权信息不在此模块暴露给客户端。
- 客户端仅通过账号密码 + 设备指纹获取服务端 JWT。
- 对称加密密钥必须稳定，避免服务重启后历史密文不可解。
"""

from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _build_stable_fernet() -> Fernet:
    """基于配置构造稳定密钥。

    Fernet 要求 32-byte urlsafe-base64 key，这里用 SHA-256 派生。
    """
    seed = settings.transport_aes_key.encode("utf-8")
    key = urlsafe_b64encode(sha256(seed).digest())
    return Fernet(key)


fernet = _build_stable_fernet()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def encrypt_text(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_text(cipher_text: str) -> str:
    return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")


def calc_device_fingerprint(raw: str) -> str:
    return sha256(raw.encode("utf-8")).hexdigest()
