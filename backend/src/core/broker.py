from faststream.redis import RedisBroker
from src.core.config import settings
from src.core.logger import logger

broker = RedisBroker(settings.REDIS_URL)


async def publish_event(message, channel: str) -> None:
    """Публикует событие, не роняя запрос при недоступности Redis.

    Уведомления — побочный эффект: если основная операция (регистрация, заказ)
    уже закоммичена, ошибка брокера не должна превращаться в 500 для клиента.
    """
    try:
        await broker.publish(message, channel=channel)
    except Exception as exc:
        logger.error(f"Не удалось опубликовать событие в '{channel}': {exc}")
