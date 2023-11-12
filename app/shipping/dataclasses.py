from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.shipping.protocols import HasDiscountRecord


@dataclass
class DiscountTransaction(HasDiscountRecord):
    """The class is for record transaction (some discount rules requires
    information about past transactions discounts)"""
    date: datetime
    carrier: str
    package_size: str
    price: Decimal
    discount: Decimal
