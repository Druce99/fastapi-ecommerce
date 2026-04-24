from sqladmin import Admin, ModelView
from src.core.database import async_engine
from src.models import UserModel, ProductModel, CategoryModel, OrderModel, OrderItemModel, ReviewModel, CartItemModel


class UserAdmin(ModelView, model=UserModel):
    column_list = [UserModel.id, UserModel.email, UserModel.role, UserModel.is_active]
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
    column_list = [ProductModel.id, ProductModel.name, ProductModel.price, ProductModel.stock, ProductModel.is_active]
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
    column_list = [OrderModel.id, OrderModel.user_id, OrderModel.status, OrderModel.total_amount, OrderModel.created_at]
    column_sortable_list = [OrderModel.id, OrderModel.created_at]
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-cart-shopping"


class ReviewAdmin(ModelView, model=ReviewModel):
    column_list = [ReviewModel.id, ReviewModel.user_id, ReviewModel.product_id, ReviewModel.grade]
    name = "Отзыв"
    name_plural = "Отзывы"
    icon = "fa-solid fa-star"


def setup_admin(app):
    admin = Admin(app, engine=async_engine, title="Админ панель")
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(ReviewAdmin)
