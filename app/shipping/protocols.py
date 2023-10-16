from asyncio import Protocol
from datetime import datetime
from decimal import Decimal
from typing import Sequence


class HasShippingPlan(Protocol):
    carrier: str
    package_size: str
    price: Decimal


class HasTransaction(Protocol):
    date: datetime
    carrier: str
    package_size: str
    price: Decimal


class HasDiscountRecord(HasTransaction, Protocol):
    discount: Decimal


class SupportsDiscountCalculate(Protocol):
    def calculate_discount(
        self,
        transaction: HasTransaction,
        shipping_plans: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        ...


class SupportsDiscountCorrection(Protocol):
    def correct_discount(
        self,
        transaction: HasTransaction,
        discount: Decimal,
        shipping_service: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        ...
