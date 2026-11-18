"""Исключения предметной области.

Здесь нет ничего про HTTP: сервисы сообщают о проблеме на языке бизнеса
(«не найдено», «нет на складе»), а в статус-коды их переводит API-слой
(см. `src/api/error_handlers.py`).
"""


class AppError(Exception):
    """Базовое исключение приложения."""

    code = "app_error"
    default_message = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


# ---------- Общие категории ----------


class NotFoundError(AppError):
    """Запрошенная сущность не существует (или недоступна пользователю)."""

    code = "not_found"
    default_message = "Resource not found"


class AlreadyExistsError(AppError):
    """Сущность с такими уникальными данными уже существует."""

    code = "already_exists"
    default_message = "Resource already exists"


class BusinessRuleError(AppError):
    """Нарушено бизнес-правило или переданы недопустимые данные."""

    code = "business_rule_violation"
    default_message = "Business rule violated"


class AuthenticationError(AppError):
    """Не удалось установить, кто делает запрос (нет/неверный/просроченный токен)."""

    code = "authentication_failed"
    default_message = "Could not validate credentials"


class PermissionDeniedError(AppError):
    """Пользователь известен, но у него нет прав на это действие."""

    code = "permission_denied"
    default_message = "Permission denied"


class InvalidFileError(AppError):
    """Загруженный файл не прошёл проверку (тип, размер)."""

    code = "invalid_file"
    default_message = "Invalid file"


class ExternalServiceError(AppError):
    """Внешний сервис (ЮKassa, S3) недоступен или вернул ошибку."""

    code = "external_service_error"
    default_message = "External service error"


class ConfigurationError(AppError):
    """Приложение настроено неправильно (например, не заданы ключи ЮKassa)."""

    code = "configuration_error"
    default_message = "Service is not configured"


# ---------- Конкретные случаи (чтобы тесты и логи были точными) ----------


class EmailAlreadyRegisteredError(AlreadyExistsError):
    code = "email_already_registered"
    default_message = "Email already registered"


class EmptyCartError(BusinessRuleError):
    code = "empty_cart"
    default_message = "Cart is empty"


class ProductUnavailableError(BusinessRuleError):
    code = "product_unavailable"

    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} is unavailable")


class InsufficientStockError(BusinessRuleError):
    code = "insufficient_stock"

    def __init__(self, product_name: str) -> None:
        super().__init__(f"Not enough stock for product {product_name}")
