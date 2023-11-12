from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import Field, StringConstraints, conset

_str_category_value = StringConstraints(
    strip_whitespace=True, min_length=1, strict=True
)
_CategoryElement = Annotated[str, _str_category_value]
_Category = conset(item_type=_CategoryElement, min_length=1)


# Alias must match mapping key names (e.g json parsed dictionary's key names) 
Limit = Annotated[Decimal, Field(gt=0, alias="limit")]
X_Times = Annotated[int, Field(gt=0, alias="x_times")]
N = Annotated[int, Field(gt=0, alias="n")]
Date = Annotated[datetime, Field(alias="date")]
Price = Annotated[Decimal, Field(gt=0, alias="price")]
PackageSize = Annotated[str, _str_category_value, Field(alias="package_size")]
Carrier = Annotated[str, _str_category_value, Field(alias="carrier")]


# Type annotation for every rule's __init__ method's argument
RULE_PARAM_TYPES: tuple[type[Any], ...] = (
    Limit,
    X_Times,
    N,
    PackageSize,
    Carrier,
)
