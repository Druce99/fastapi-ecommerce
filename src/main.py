from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.api import categories, products, reviews, users, cart, orders
from src.admin import setup_admin

app = FastAPI(
    title="FastAPI Интернет-магазин",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
