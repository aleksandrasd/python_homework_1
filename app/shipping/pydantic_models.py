from sqlite3 import Date
from typing import Annotated, Any, Mapping

from pydantic import BaseModel, StringConstraints

from app.shipping.pydantic_types import Carrier, PackageSize, Price

_str_value = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, strict=True)
]


class RuleModel(BaseModel):
    """Discount rule schema model. Additional validation for `params` mapping
    is needed.
    
    Attributes:
      name: discount rule name
      params: discount rule initiation parameters (passed to rule's __init__
              method)"""

    name: _str_value
    params: Mapping[_str_value, Any]


class ShippingModel(BaseModel):
    """Shipping plan entry model. Categorical values require additional
    validation"""

    package_size: PackageSize
    carrier: Carrier
    price: Price


class TransactionModel(BaseModel):
    """Transaction model. Categorical values require additional validation"""

    package_size: PackageSize
    carrier: Carrier
    date: Date
