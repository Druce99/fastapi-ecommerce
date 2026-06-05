from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Настройки приложения."""

    # ---------- База данных ----------
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DB_NAME: str = Field(default="ecommerce_db", env="DB_NAME")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ---------- JWT ----------
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY",
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # ---------- Redis ----------
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # ---------- Приложение ----------
    APP_NAME: str = Field(default="E-commerce API", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=True, env="DEBUG")
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5173"],
        env="ALLOWED_ORIGINS",
    )

    # ---------- Админка ----------
    ADMIN_USERNAME: str = Field(default="admin", env="ADMIN_USERNAME")
    ADMIN_PASSWORD: str = Field(default="changeme", env="ADMIN_PASSWORD")

    # ---------- S3 ----------
    S3_BUCKET_NAME: str = Field(default="", env="S3_BUCKET_NAME")
    S3_ACCESS_KEY: str = Field(default="", env="S3_ACCESS_KEY")
    S3_SECRET_KEY: str = Field(default="", env="S3_SECRET_KEY")
    S3_ENDPOINT_URL: str = Field(default="https://storage.yandexcloud.net", env="S3_ENDPOINT_URL")
    
    # ---------- ЮKassa ----------
    YOOKASSA_SHOP_ID: int = Field(default=0, env="YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: str = Field(default="", env="YOOKASSA_SECRET_KEY")
    YOOKASSA_RETURN_URL: str = Field(default="https://druceshop.ru", env="YOOKASSA_RETURN_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()