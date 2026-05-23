from src.schemas.messages import OrderCreated, UserRegistered
from src.core.broker import broker
from src.core.logger import logger

@broker.subscriber("order_created")
async def handle_order_created(data: OrderCreated):
    logger.info(f"Отправка письма о заказе #{data.order_id} на {data.email}")

@broker.subscriber("user_registered")
async def handle_user_registered(data: UserRegistered):
    logger.info(f"Приветственное письмо отправлено на {data.email}")