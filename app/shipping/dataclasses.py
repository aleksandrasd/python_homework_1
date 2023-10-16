from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.shipping.protocols import (
    HasDiscountRecord,
    HasShippingPlan,
    HasTransaction,
)


@dataclass
class ShippingPlan(HasShippingPlan):
    carrier: str
    package_size: str
    price: Decimal


@dataclass
class Transaction(HasTransaction):
    date: datetime
    carrier: str
    package_size: str
    price: Decimal


@dataclass
class DiscountTransaction(HasDiscountRecord):
    date: datetime
    carrier: str
    package_size: str
    price: Decimal
    discount: Decimal


@dataclass
class History(HasDiscountRecord):
    discount: Decimal
    date: datetime
    carrier: str
    package_size: str
