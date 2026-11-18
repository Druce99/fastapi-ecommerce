from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET = "your-secret-key-here-change-in-production"
_INSECURE_ADMIN_PASSWORD = "changeme"


class Settings(BaseSettings):
    """Настройки приложения. Значения читаются из переменных окружения / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- База данных ----------
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "ecommerce_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ---------- JWT ----------
    SECRET_KEY: str = _INSECURE_SECRET
    # Отдельный ключ подписи cookie-сессии админки (не тот же, что для JWT)
    SESSION_SECRET_KEY: str = _INSECURE_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Стоимость bcrypt (2^N итераций). В production 12; в тестах понижается до 4 ради скорости
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=31)

    # ---------- Redis ----------
    REDIS_URL: str = "redis://localhost:6379"

    # ---------- Приложение ----------
    APP_NAME: str = "E-commerce API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    # JSON-список, например: ["https://example.com"]
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # ---------- Админка ----------
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = _INSECURE_ADMIN_PASSWORD

    # ---------- S3 ----------
    S3_BUCKET_NAME: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_ENDPOINT_URL: str = "https://storage.yandexcloud.net"

    # ---------- ЮKassa ----------
    YOOKASSA_SHOP_ID: int = 0
    YOOKASSA_SECRET_KEY: str = ""
    YOOKASSA_RETURN_URL: str = "http://localhost:8000/docs"

    @model_validator(mode="after")
    def _forbid_insecure_defaults_in_production(self) -> "Settings":
        """В production (DEBUG=False) не даём стартовать с дефолтными секретами."""
        if not self.DEBUG:
            if self.SECRET_KEY == _INSECURE_SECRET:
                raise ValueError("SECRET_KEY не задан: укажите уникальное значение в .env")
            if self.SESSION_SECRET_KEY in (_INSECURE_SECRET, self.SECRET_KEY):
                raise ValueError(
                    "SESSION_SECRET_KEY не задан или совпадает с SECRET_KEY: "
                    "укажите отдельное уникальное значение в .env"
                )
            if self.ADMIN_PASSWORD == _INSECURE_ADMIN_PASSWORD:
                raise ValueError("ADMIN_PASSWORD не задан: укажите пароль админки в .env")
        return self


settings = Settings()
