import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.admin import setup_admin
from src.api import cart, categories, orders, payments, products, reviews, users
from src.api.error_handlers import register_error_handlers
from src.core.broker import broker
from src.core.config import settings
from src.core.logger import logger
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    yield
    await broker.stop()


app = FastAPI(
    title="FastAPI Интернет-магазин",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    log_id = str(uuid4())
    start_time = time.time()
    with logger.contextualize(log_id=log_id):
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            if response.status_code in [401, 402, 403, 404]:
                logger.warning(f"Request to {request.url.path} failed in {duration:.3f}s")
            else:
                logger.info(f"Successfully accessed {request.url.path} in {duration:.3f}s")
        except Exception:
            # Пишем полный traceback с log_id и пробрасываем дальше:
            # клиентский ответ формирует unhandled_error_handler.
            logger.exception(f"Request to {request.url.path} failed")
            raise
        return response


register_error_handlers(app)

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)

setup_admin(app)


@app.get("/")
async def root() -> dict:
    return {"message": "Добро пожаловать в API интернет-магазина!"}
