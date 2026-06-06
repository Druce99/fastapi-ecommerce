import ipaddress
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import json
from yookassa.domain.notification import WebhookNotification
from sqlalchemy import select
from src.models import OrderModel

from src.core.database import get_async_db
from src.repository.orders import OrderRepository

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

YOOKASSA_NETWORKS = [
    ipaddress.ip_network("185.71.76.0/27"),
    ipaddress.ip_network("185.71.77.0/27"),
    ipaddress.ip_network("77.75.153.0/25"),
    ipaddress.ip_network("77.75.156.11/32"),
    ipaddress.ip_network("77.75.156.35/32"),
    ipaddress.ip_network("77.75.154.128/25"),
    ipaddress.ip_network("2a02:5180::/32"),
]

def is_yookassa_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in network for network in YOOKASSA_NETWORKS)
    except ValueError:
        return False

def _extract_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None

@router.post("/yookassa/webhook", status_code=status.HTTP_200_OK)
async def yookassa_webhook(request: Request, db: AsyncSession = Depends(get_async_db)):
    client_ip = _extract_client_ip(request)
    if not client_ip or not is_yookassa_ip(client_ip):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="IP not Allowed")
    
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {exc}")
    
    try:
        notification = WebhookNotification(payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid notification: {exc}")
    
    payment = notification.object
    order_id = payment.metadata.get("order_id") if payment.metadata else None
    
    if not order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing order id")
    
    result = await db.scalars(select(OrderModel).where(OrderModel.id == int(order_id)))
    order = result.first()
    if order is None:
        return {"status": "ignored"}
    if payment.status == "succeeded":
        if not order.paid_at:
            order.status = "paid"
            order.paid_at = datetime.now(timezone.utc)
            order.payment_id = payment.id
    elif payment.status == "canceled":
        order.status = "canceled"
    
    await db.commit()
    return {"status": "ok"}