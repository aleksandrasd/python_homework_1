"""Provides callables for variables validation

Provides callables for validating variable's type and value and also keeps
a map of variable names with their validation callables."""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

logger = logging.getLogger(__name__)


def get_validators(
    categories: Mapping[str, Sequence[str]]
) -> Mapping[str, list[Callable[..., Any]]]:
    """Get variables' validation callables.

    Args:
        categories: category names mapped to category's list of elements

    Returns:
        Variables' names mapped to variables' validation callables.
    """
    _validate_categories_schema(categories)

    for key in categories:
        expect_type(str)(*categories[key])

    return {
        "carrier": [validate_category(categories["carrier"])],
        "package_size": [validate_category(categories["package_size"])],
        "price": [expect_type(Decimal), positive_number],
        "x_times": [expect_type(int), positive_number],
        "n": [expect_type(int), positive_number],
        "limit": [expect_type(Decimal), positive_number],
        "date": [expect_type(datetime)],
    }


def expect_type(*expected_types: type) -> Callable[..., None]:
    def _expect_type(*args) -> None:
        for value in args:
            if not isinstance(value, tuple(expected_types)):
                text_expect_type = " or ".join(
                    e.__name__ for e in expected_types
                )
                raise TypeError(
                    (
                        f"expected type to be {text_expect_type}, not"
                        f" {type(value).__name__}."
                    )
                )

    return _expect_type


def validate_category(category_elements: Sequence[str]) -> Callable[..., None]:
    expect_type(str)(*category_elements)

    def _validate(*args):
        for arg in args:
            if arg not in category_elements:
                raise ValueError(
                    (
                        f"element {arg} does not belong to category"
                        f" {category_elements}."
                    )
                )

    return _validate


def positive_number(x: float | int | Decimal) -> None:
    if x <= 0:
        raise ValueError("expected positive number.")


def validate_args(
    params: Mapping[str, Any],
    validators: Mapping[str, Sequence[Callable[[Any], Any]]],
) -> None:
    """Validate callable's arguments.

    Args:
        params: callable's arguments' names and their values.
        validators: contains arguments names' and their corresponding
                    validation callables.

    Raises:
        AttributeError: raised if missing validator for specific argument.
    """
    for arg_name, arg_value in params.items():
        if arg_name not in validators:
            raise AttributeError(
                f"missing validator for variable {arg_name!r}."
            )
        for validator in validators[arg_name]:
            try:
                validator(arg_value)
            except ValueError as e:
                raise ValueError(
                    (
                        "failed to validate value: argument name:"
                        f" {arg_name!r}, value: {arg_value!r}."
                    )
                ) from e
            except TypeError as e:
                raise TypeError(
                    (
                        "failed to validate type: argument name:"
                        f" {arg_name!r}, value: {arg_value!r}."
                    )
                ) from e


def _validate_categories_schema(x) -> None:
    if not isinstance(x, Mapping):
        raise TypeError(
            (
                "categories must be stored in a mapping"
                f" not {type(x).__name__}"
            )
        )
    try:
        keys = list(key for key in x)
        expect_type(str)(*keys)
        values = list(x[key] for key in x)
        expect_type(list)(*values)
    except TypeError as e:
        raise TypeError("categories have invalid mapping structure") from e
