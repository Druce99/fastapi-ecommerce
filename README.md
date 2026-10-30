fastapi-ecommerce

Backend интернет-магазина на FastAPI: каталог с деревом категорий, корзина, заказы, отзывы, JWT-авторизация, оплата через ЮKassa и админ-панель.

Стек
Python 3.13, FastAPI, Pydantic v2
PostgreSQL 16, async SQLAlchemy 2 (asyncpg), Alembic
Redis 7 + FastStream (события order_created, user_registered)
JWT (access и refresh токены), пароли хешируются bcrypt
S3-совместимое хранилище для изображений (aioboto3)
ЮKassa (создание платежа и webhook)
SQLAdmin (админ-панель)
Docker Compose, nginx, gunicorn + uvicorn workers
GitHub Actions: деплой на VPS по SSH при пуше в main
pytest, pytest-asyncio, httpx
Что умеет
Пользователи: регистрация, вход, обновление токена, роли (смена роли доступна администратору).
Категории: дерево категорий (/categories/tree), CRUD.
Товары: CRUD, список с пагинацией, товары по категории, полнотекстовый поиск (PostgreSQL tsvector), рейтинг.
Отзывы: создание и удаление, отзывы по товару.
Корзина: добавить, изменить количество, удалить позицию, очистить.
Заказы: оформление (/orders/checkout) с созданием платежа, список и просмотр заказа.
Оплата: webhook ЮKassa (/payments/yookassa/webhook) обновляет статус заказа.
Админ-панель: /admin (за basic-auth на уровне nginx).

Интерактивная документация API: /docs.

Архитектура
backend/src/
  api/          роутеры FastAPI
  service/      бизнес-логика
  repository/   доступ к БД
  models/       модели SQLAlchemy
  schemas/      схемы Pydantic
  core/         конфиг, БД, безопасность, брокер, логирование
  tasks/        обработчики событий FastStream
  migrations/   миграции Alembic

Слои: роутер → сервис → репозиторий → БД.

Запуск
bash
git clone https://github.com/Druce99/fastapi-ecommerce.git
cd fastapi-ecommerce
cp .env.example .env      # заполните значения
docker compose up --build

При старте контейнер применяет миграции (alembic upgrade head) и запускает gunicorn на порту 8000. После запуска: http://localhost:8000/docs

Переменные окружения

Полный список в .env.example. Основные: DB_* (подключение к PostgreSQL), SECRET_KEY (подпись JWT), REDIS_URL, S3_* (хранилище изображений), YOOKASSA_* (платежи). Файл .env в репозиторий не коммитится.

Тесты
bash
cd backend
uv run pytest

Покрыты категории, товары, отзывы, пользователи (55 тестов). Корзина, заказы и платежи тестами пока не покрыты.
