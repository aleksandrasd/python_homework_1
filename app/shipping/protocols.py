from datetime import datetime
from decimal import Decimal
from sqlite3 import Date
from typing import Iterable, Protocol, runtime_checkable

from app.shipping.pydantic_types import Carrier, PackageSize


@runtime_checkable
class HasShippingPlan(Protocol):
    carrier: str
    package_size: str
    price: Decimal


@runtime_checkable
class HasTransaction(Protocol):
    date: datetime | Date
    carrier: str | Carrier
    package_size: str | PackageSize


@runtime_checkable
class HasDiscountRecord(HasTransaction, Protocol):
    discount: Decimal


@runtime_checkable
class SupportsDiscountCalculate(Protocol):
    """Every discount rule implements this protocol"""

    def calculate_discount(
        self,
        transaction: HasTransaction,
        price: Decimal,
        shipping_plans: Iterable[HasShippingPlan],
        history: Iterable[HasDiscountRecord],
    ) -> Decimal:
        """Calculates discount (if any)

        Args:
            transaction: transaction details
            price: price before discount
            shipping_plans: shipping plans
            history: transaction details with applied discount

        Returns:
            Decimal: discount size
        """
        ...


@runtime_checkable
class SupportsDiscountCorrection(Protocol):
    """Every discount correction rule implements this protocol"""

    def correct_discount(
        self,
        transaction: HasTransaction,
        discount: Decimal,
        shipping_service: Iterable[HasShippingPlan],
        history: Iterable[HasDiscountRecord],
    ) -> Decimal:
        ...
