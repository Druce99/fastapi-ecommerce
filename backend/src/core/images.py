import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aioboto3
from fastapi import HTTPException, UploadFile, status

from src.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024

@asynccontextmanager
async def get_s3_client():
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    ) as client:
        yield client

async def save_product_image(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPG, PNG or WebP images are allowed")
    
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image is too large")
    
    extension = Path(file.filename or "").suffix.lower() or ".jpg"
    file_name = f"products/{uuid.uuid4()}{extension}"
    
    async with get_s3_client() as s3:
        await s3.put_object(
            Bucket = settings.S3_BUCKET_NAME,
            Key = file_name,
            Body=content,
            ContentType=file.content_type,
        )
    return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{file_name}"

async def remove_product_image(url: str | None) -> None:
    if not url:
        return
    key = url.split(f"{settings.S3_BUCKET_NAME}/")[-1]
    async with get_s3_client() as s3:
        await s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)