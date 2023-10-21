"""Provides variable cast callables and keeps list of variables that needs
to be casted.

Provides callables for casting from one class to another class and also keeps
dictionary of variables names that needs to be casted to different class
mapped to callables that does the casting.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Mapping

from app.shipping.logging import add_trace_logging_level_if_not_exists

add_trace_logging_level_if_not_exists()
logger = logging.getLogger(__name__)


def cast_args(
    params: Mapping[str, Any], casters: Mapping[str, Callable[[Any], Any]]
) -> Mapping[str, Any]:
    """Cast callable's arguments.

    Args:
        params: callable's arguments' names and
                and their corresponding values.

        casters: contains arguments names' and their corresponding
                 casting functions.

    Returns:
        Passed arguments with their corresponding values. If casting
        callable was provided for specific argument, then
        then that specific argument's value was casted and
        returned instead of original value.
    """
    casted_params = {}
    for arg_name, arg_value in params.items():
        if arg_name in casters:
            new_arg_value = casters[arg_name](arg_value)
        else:
            new_arg_value = arg_value
        casted_params.update({arg_name: new_arg_value})
    return casted_params


def cast_to_decimal(x: str) -> Decimal:
    if not isinstance(x, str):
        raise TypeError(
            (
                "Number must be string to cast as Decimal not "
                f"{type(x).__name__}"
            )
        )
    return Decimal(x)


# Map of variables names that needs to be casted to different class and
# callables that do the casting.
CASTERS: dict[str, Callable[[Any], Any]] = {
    "price": cast_to_decimal,
    "date": datetime.fromisoformat,
    "limit": cast_to_decimal,
}
