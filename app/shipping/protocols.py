from datetime import datetime
from decimal import Decimal
from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class HasShippingPlan(Protocol):
    carrier: str
    package_size: str
    price: Decimal


@runtime_checkable
class HasTransaction(Protocol):
    date: datetime
    carrier: str
    package_size: str
    price: Decimal


@runtime_checkable
class HasDiscountRecord(HasTransaction, Protocol):
    discount: Decimal


@runtime_checkable
class SupportsDiscountCalculate(Protocol):
    def calculate_discount(
        self,
        transaction: HasTransaction,
        shipping_plans: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        ...


@runtime_checkable
class SupportsDiscountCorrection(Protocol):
    def correct_discount(
        self,
        transaction: HasTransaction,
        discount: Decimal,
        shipping_service: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        ...
