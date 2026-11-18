from fastapi import APIRouter, Request, status
from src.api.dependencies import OrderServiceDep
from src.core.exceptions import BusinessRuleError

router = APIRouter(prefix="/payments", tags=["payments"])

_PAYMENT_EVENT_PREFIX = "payment."


@router.post("/yookassa/webhook", status_code=status.HTTP_200_OK)
async def yookassa_webhook(request: Request, service: OrderServiceDep) -> dict[str, str]:
    """Уведомление ЮKassa о платеже.

    Тело запроса не считается доверенным: из него берётся только id платежа, а реальное
    состояние платежа сервис запрашивает у ЮKassa. Любой неожиданный или чужой запрос
    поэтому безвреден. Ответ 2xx означает «принято», 5xx заставит ЮKassa повторить доставку.
    """
    try:
        payload = await request.json()
    except ValueError as exc:
        raise BusinessRuleError("Invalid JSON") from exc

    event = payload.get("event") if isinstance(payload, dict) else None
    payment_object = payload.get("object") if isinstance(payload, dict) else None
    payment_id = payment_object.get("id") if isinstance(payment_object, dict) else None

    if not isinstance(event, str) or not isinstance(payment_id, str) or not payment_id:
        raise BusinessRuleError("Invalid notification")

    # Нас интересуют только события платежей (возвраты и т. п. пока не обрабатываем)
    if not event.startswith(_PAYMENT_EVENT_PREFIX):
        return {"status": "ignored"}

    await service.handle_payment_notification(payment_id)
    return {"status": "ok"}
