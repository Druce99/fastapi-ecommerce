from decimal import Decimal
from typing import Any
from uuid import uuid4

from anyio import to_thread
from yookassa import Configuration, Payment

from src.core.config import settings

async def create_yookassa_payment(
    *,
    order_id: int,
    amount: Decimal,
    user_email: str,
    description: str,
) -> dict[str, Any]:
    
    # 1. Проверка настроек (fallback на ошибку)
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        raise RuntimeError("Задайте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env")
    
    # 2. Глобальная настройка SDK (Basic Auth под капотом)
    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
    
    # 3. ФОРМИРОВАНИЕ PAYLOAD
    # Это JSON для POST /v3/payments.
    payload = {
        "amount": {  # Сумма платежа
            "value": f"{amount:.2f}",  # str(Decimal) — обязательно строка! "100.00"
            "currency": "RUB",
        },
        "confirmation": {  # Как подтвердить платеж
            "type": "redirect",  # Пользователь редиректится на форму YooKassa
            "return_url": settings.YOOKASSA_RETURN_URL,  # Куда вернуть после оплаты
        },
        "capture": True,  # Авто-списание денег после авторизации
        "description": description,  # Видно пользователю в истории
        "metadata": {  # Ваши данные (сохраняются в платеже)
            "order_id": order_id,  # Связь с заказом из БД
        },
        "receipt": {  # ФИСКальный ЧЕК (обязателен по 54-ФЗ для РФ!)
            "customer": {  # Данные плательщика
                "email": user_email,  # Чек придет на email
            },
            "items": [
            # Список "товаров"/услуг (здесь 1 item = весь наш заказ)
            #Но также мы можем передать и каждую позицию отдельно.
                {
                    "description": description[:128],  # Макс. 128 символов!
                    "quantity": "1.00",  # Кол-во (строка)
                    "amount": {  # Сумма item
                        "value": f"{amount:.2f}",
                        "currency": "RUB",
                    },
                    "vat_code": 1,  # НДС: 1=без НДС (0%), 2=0%, 3=10%, 4=20%, 5=расчетный, 6=спецрежим
                    "payment_mode": "full_prepayment",  # Режим: полная предоплата
                    "payment_subject": "commodity",  # Тип: "service"=услуга, "commodity"=товар или заказ
                },
            ],
        },
    }
    
    # 4. Вспомогательная синхронная функция для создания платежа
    def _request() -> Payment:
        return Payment.create(payload, str(uuid4()))
    
    # 5. Вызов в thread
    payment: Payment = await to_thread.run_sync(_request)
    
    #6. Извлечение URL для оплаты
    confirmation_url = getattr(payment.confirmation, "confirmation_url", None)
    
    # 7. Возврат данных для фронта/БД
    return {
        "id": payment.id,
        "status": payment.status,
        "confirmation_url":confirmation_url
    }
