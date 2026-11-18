import sys

from loguru import logger

logger.remove()
logger.configure(extra={"log_id": "-"})
# Логи пишем в stdout — их собирает Docker (`docker compose logs`).
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[log_id]} | {message}",
    level="INFO",
    enqueue=True,
)
