from loguru import logger
logger.remove()
logger.add("logs/app.log", format="{time} | {level} | {extra[log_id]} | {message}", level="INFO", rotation="10 MB", enqueue=True)