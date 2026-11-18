import secrets

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from src.core.config import settings
from src.core.database import async_engine
from src.models import CategoryModel, OrderModel, ProductModel, ReviewModel, UserModel
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

ADMIN_SESSION_MAX_AGE = 8 * 60 * 60  # 8 часов


class AdminAuth(AuthenticationBackend):
    """Вход в админку по логину и паролю из настроек (ADMIN_USERNAME / ADMIN_PASSWORD)."""

    def __init__(self) -> None:
        super().__init__(secret_key=settings.SESSION_SECRET_KEY)
        # Свой SessionMiddleware с защитными флагами cookie
        self.middlewares = [
            Middleware(
                SessionMiddleware,
                secret_key=settings.SESSION_SECRET_KEY,
                https_only=not settings.DEBUG,
                same_site="strict",
                max_age=ADMIN_SESSION_MAX_AGE,
            )
        ]

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", "")).encode()
        password = str(form.get("password", "")).encode()
        # Сравнение за постоянное время; обе проверки выполняются всегда
        username_ok = secrets.compare_digest(username, settings.ADMIN_USERNAME.encode())
        password_ok = secrets.compare_digest(password, settings.ADMIN_PASSWORD.encode())
        if username_ok and password_ok:
            request.session.update({"admin": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin"))


class UserAdmin(ModelView, model=UserModel):
    column_list = [UserModel.id, UserModel.email, UserModel.role, UserModel.is_active]
    # Хеш пароля не показываем и не даём править; пользователей создаёт регистрация через API
    form_columns = [UserModel.email, UserModel.role, UserModel.is_active]
    can_create = False
    can_delete = False  # вместо удаления снимайте флаг is_active
    column_searchable_list = [UserModel.email]
    column_sortable_list = [UserModel.id, UserModel.role]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"


class CategoryAdmin(ModelView, model=CategoryModel):
    column_list = [CategoryModel.id, CategoryModel.name, CategoryModel.is_active]
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-list"


class ProductAdmin(ModelView, model=ProductModel):
    column_list = [
        ProductModel.id,
        ProductModel.name,
        ProductModel.price,
        ProductModel.stock,
        ProductModel.is_active,
    ]
    column_searchable_list = [ProductModel.name]
    column_sortable_list = [ProductModel.id, ProductModel.price, ProductModel.stock]
    form_columns = [
        ProductModel.name,
        ProductModel.description,
        ProductModel.price,
        ProductModel.stock,
        ProductModel.image_url,
        ProductModel.is_active,
        ProductModel.category,
        ProductModel.seller,
    ]
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"


class OrderAdmin(ModelView, model=OrderModel):
    column_list = [
        OrderModel.id,
        OrderModel.user_id,
        OrderModel.status,
        OrderModel.total_amount,
        OrderModel.created_at,
    ]
    column_sortable_list = [OrderModel.id, OrderModel.created_at]
    # Только просмотр: статусы меняет платёжный поток (webhook), а не ручная правка
    can_create = False
    can_edit = False
    can_delete = False
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-cart-shopping"


class ReviewAdmin(ModelView, model=ReviewModel):
    column_list = [ReviewModel.id, ReviewModel.user_id, ReviewModel.product_id, ReviewModel.grade]
    # Только просмотр: изменения отзывов должны пересчитывать рейтинг товара (это делает API)
    can_create = False
    can_edit = False
    can_delete = False
    name = "Отзыв"
    name_plural = "Отзывы"
    icon = "fa-solid fa-star"


def setup_admin(app: FastAPI) -> None:
    admin = Admin(
        app,
        engine=async_engine,
        title="Админ панель",
        authentication_backend=AdminAuth(),
    )
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(ReviewAdmin)
