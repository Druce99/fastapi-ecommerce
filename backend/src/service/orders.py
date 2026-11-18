from datetime import UTC, datetime
from decimal import Decimal

from src.core.broker import publish_event
from src.core.exceptions import (
    ConfigurationError,
    EmptyCartError,
    ExternalServiceError,
    InsufficientStockError,
    NotFoundError,
    ProductUnavailableError,
)
from src.core.logger import logger
from src.models import OrderItemModel, OrderModel, OrderStatus
from src.repository.uow import AbstractUnitOfWork, UnitOfWorkFactory
from src.schemas import OrderCreatedSchema, OrderListSchema
from src.schemas.orders import OrderCheckoutResponse
from src.service.payments import PaymentInfo, create_yookassa_payment, fetch_yookassa_payment


class OrderService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def checkout(self, user_id: int, email: str) -> OrderCheckoutResponse:
        """Оформление заказа тремя короткими транзакциями.

        1. Резерв: блокируем товары, списываем остаток, создаём заказ `pending` → commit.
        2. Платёж в ЮKassa выполняется ВНЕ транзакции (блокировки уже сняты).
        3. Фиксация: сохраняем payment_id и очищаем корзину → commit.

        Если на шаге 2 или 3 что-то пошло не так, заказ отменяется, а остатки возвращаются
        (компенсирующая транзакция), и клиент получает ошибку.
        """
        order_id, total_amount = await self._reserve(user_id)

        try:
            payment_info = await create_yookassa_payment(
                order_id=order_id,
                amount=total_amount,
                user_email=email,
                description=f"Заказ №{order_id} в DruceShop",
            )
        except RuntimeError as exc:
            # Наша ошибка — неправильные настройки
            await self._compensate(order_id)
            raise ConfigurationError(str(exc)) from exc
        except Exception as exc:
            # Внешняя ошибка — ЮKassa недоступна
            await self._compensate(order_id)
            raise ExternalServiceError(str(exc)) from exc

        try:
            order = await self._attach_payment(order_id, user_id, payment_info["id"])
        except Exception:
            # Платёж создан, но сохранить его не удалось: клиент ссылку не получит,
            # поэтому заказ отменяем и возвращаем товар.
            await self._compensate(order_id)
            raise

        # Уведомление после фиксации; сбой брокера не ломает ответ
        await publish_event(
            OrderCreatedSchema(order_id=order.id, email=email),
            channel="order_created",
        )
        return OrderCheckoutResponse(
            order=order,
            confirmation_url=payment_info.get("confirmation_url"),
        )

    async def cancel_pending_order(self, order_id: int) -> bool:
        """Отменить неоплаченный заказ и вернуть товар на склад.

        Идемпотентно: заказ не в статусе `pending` не трогаем (возвращаем False).
        Используется при сбое checkout, а позже — webhook ЮKassa и очисткой «зависших» заказов.
        """
        async with self._uow_factory() as uow:
            order = await uow.orders.get_by_id_with_items(order_id, lock=True)
            if order is None or order.status != OrderStatus.PENDING:
                return False

            await self._cancel_locked_order(uow, order)
            await uow.commit()
        return True

    async def handle_payment_notification(self, payment_id: str) -> None:
        """Обработать уведомление ЮKassa о платеже.

        Из уведомления берём только id платежа; статус, сумму и номер заказа запрашиваем
        у ЮKassa сами, поэтому подделанное уведомление ничего изменить не может.
        Метод идемпотентен: повторное уведомление не меняет уже достигнутое состояние.
        """
        try:
            payment = await fetch_yookassa_payment(payment_id)
        except RuntimeError as exc:
            raise ConfigurationError(str(exc)) from exc
        except Exception as exc:
            # Ошибка пробрасывается как 5xx: ЮKassa повторит уведомление позже
            raise ExternalServiceError(str(exc)) from exc

        if payment.order_id is None:
            logger.warning(f"Платёж {payment.id} без order_id в metadata: игнорируем")
            return

        if payment.status == "succeeded":
            await self._mark_paid(payment)
        elif payment.status == "canceled":
            await self._cancel_for_payment(payment)
        # остальные статусы (pending, waiting_for_capture) состояния заказа не меняют

    async def get_order(self, user_id: int, order_id: int) -> OrderModel:
        async with self._uow_factory() as uow:
            order = await uow.orders.get_by_id_with_items(order_id=order_id)
        if not order or order.user_id != user_id:
            raise NotFoundError("Order not found")
        return order

    async def list_orders(self, user_id: int, page: int, page_size: int) -> OrderListSchema:
        async with self._uow_factory() as uow:
            total = await uow.orders.count_user_orders(user_id=user_id)
            orders = await uow.orders.get_user_orders(
                user_id=user_id, offset=(page - 1) * page_size, limit=page_size
            )
        return OrderListSchema(items=orders, total=total, page=page, page_size=page_size)

    # ========== Обработка платежей ==========

    @staticmethod
    def _payment_matches_order(order: OrderModel | None, payment: PaymentInfo) -> bool:
        """Платёж относится к заказу: тот же payment_id, сумма и валюта."""
        if order is None:
            logger.warning(f"Платёж {payment.id}: заказ {payment.order_id} не найден")
            return False
        if order.payment_id != payment.id:
            logger.warning(f"Платёж {payment.id} не принадлежит заказу {order.id}: игнорируем")
            return False
        if payment.currency != "RUB" or payment.amount != order.total_amount:
            logger.error(
                f"Сумма платежа {payment.id} ({payment.amount} {payment.currency}) "
                f"не совпадает с заказом {order.id} ({order.total_amount}): игнорируем"
            )
            return False
        return True

    async def _mark_paid(self, payment: PaymentInfo) -> None:
        """pending → paid. Оплаченный заказ повторно не трогаем."""
        async with self._uow_factory() as uow:
            order = await uow.orders.get_by_id_with_items(payment.order_id, lock=True)
            if not self._payment_matches_order(order, payment):
                return
            if order.status == OrderStatus.PAID:
                return
            if order.status == OrderStatus.CANCELED:
                logger.error(
                    f"Платёж {payment.id} успешен, но заказ {order.id} уже отменён: "
                    "нужен ручной возврат денег"
                )
                return

            order.status = OrderStatus.PAID.value
            order.paid_at = datetime.now(UTC)
            await uow.commit()

    async def _cancel_for_payment(self, payment: PaymentInfo) -> None:
        """Платёж отменён: pending → canceled с возвратом остатков. Оплаченный заказ не отменяем."""
        async with self._uow_factory() as uow:
            order = await uow.orders.get_by_id_with_items(payment.order_id, lock=True)
            if not self._payment_matches_order(order, payment):
                return
            if order.status != OrderStatus.PENDING:
                return

            await self._cancel_locked_order(uow, order)
            await uow.commit()

    @staticmethod
    async def _cancel_locked_order(uow: AbstractUnitOfWork, order: OrderModel) -> None:
        """Вернуть товар на склад и пометить заказ отменённым (заказ уже заблокирован)."""
        product_ids = sorted({item.product_id for item in order.items})
        products = await uow.products.get_by_ids_for_update(product_ids)
        product_map = {p.id: p for p in products}
        for item in order.items:
            product_map[item.product_id].stock += item.quantity
        order.status = OrderStatus.CANCELED.value

    # ========== Фазы checkout ==========

    async def _reserve(self, user_id: int) -> tuple[int, Decimal]:
        """Транзакция 1: проверка корзины, резерв остатков, создание заказа `pending`."""
        async with self._uow_factory() as uow:
            cart_items = await uow.cart.get_cart_items(user_id=user_id)
            if not cart_items:
                raise EmptyCartError

            # Блокируем товары от гонки (SELECT FOR UPDATE, порядок по id)
            product_ids = [item.product_id for item in cart_items]
            products = await uow.products.get_by_ids_for_update(product_ids)
            product_map = {p.id: p for p in products}

            order = OrderModel(user_id=user_id, status=OrderStatus.PENDING.value)
            total_amount = Decimal("0")

            for cart_item in cart_items:
                product = product_map.get(cart_item.product_id)
                if not product or not product.is_active:
                    raise ProductUnavailableError(cart_item.product_id)
                if product.stock < cart_item.quantity:
                    raise InsufficientStockError(product.name)

                unit_price = product.price
                total_price = unit_price * cart_item.quantity
                total_amount += total_price
                order.items.append(
                    OrderItemModel(
                        product_id=cart_item.product_id,
                        quantity=cart_item.quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                    )
                )
                product.stock -= cart_item.quantity
            order.total_amount = total_amount

            # add() делает flush: заказ получает id
            await uow.orders.add(order)
            await uow.commit()
            return order.id, total_amount

    async def _attach_payment(self, order_id: int, user_id: int, payment_id: str) -> OrderModel:
        """Транзакция 2: сохранить payment_id, очистить корзину, вернуть заказ для ответа."""
        async with self._uow_factory() as uow:
            order = await uow.orders.get_by_id_with_items(order_id, lock=True)
            if order is None:
                raise NotFoundError("Order not found")
            order.payment_id = payment_id
            await uow.cart.clear_cart(user_id=user_id)
            await uow.commit()

            # Повторная загрузка подтягивает значения, которые база проставила сама (updated_at)
            refreshed = await uow.orders.get_by_id_with_items(order_id)
            if refreshed is None:
                raise NotFoundError("Order not found")
            return refreshed

    async def _compensate(self, order_id: int) -> None:
        """Компенсация: отменить заказ и вернуть остатки. Ошибки компенсации только логируем,
        чтобы не затереть исходную причину сбоя (зависший заказ подберёт фоновая очистка)."""
        try:
            await self.cancel_pending_order(order_id)
        except Exception:
            logger.exception(f"Не удалось отменить заказ {order_id} после сбоя checkout")
