from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from uuid import uuid4
from contextlib import asynccontextmanager

from src.api import categories, products, reviews, users, cart, orders
from src.admin import setup_admin
from src.core.logger import logger
from src.core.broker import broker
import src.tasks.notifications

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        except Exception as ex:
            logger.error(f"Request to {request.url.path} failed: {ex}")
            response = JSONResponse(content={"success": False}, status_code=500)
        return response

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)

app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

setup_admin(app)

@app.get("/")
async def root() -> dict:
    return {"message": "Добро пожаловать в API интернет-магазина!"}
