from faststream.redis  import RedisBroker
from src.core.config import settings
broker = RedisBroker(settings.REDIS_URL)