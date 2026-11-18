from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS
)


# ========== Хеширование паролей ==========
def hash_password(password: str) -> str:
    """Преобразует пароль в хеш с использованием bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли введённый пароль сохранённому хешу."""
    return pwd_context.verify(plain_password, hashed_password)


# ========== Создание токенов ==========
def create_access_token(data: dict) -> str:
    """Создаёт JWT с payload (sub, role, id, exp)."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Создаёт refresh-токен с длительным сроком действия и token_type="refresh"."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
