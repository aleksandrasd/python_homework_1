import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

logger = logging.getLogger(__name__)


def get_validators(
    categories: Mapping[str, Sequence[str]]
) -> dict[str, list[Callable[..., Any]]]:
    if not isinstance(categories, Mapping):
        raise TypeError(f"expected mapping not {type(categories).__name__}")

    for key in categories:
        expect_type(str)(*categories[key])

    return {
        "carrier": [validate_category(categories["carrier"])],
        "package_size": [validate_category(categories["package_size"])],
        "price": [expect_type(Decimal), positive_number],
        "n_times": [expect_type(int), positive_number],
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
    """Validate function's/method's arguments.

    Args:
        params: method's/function's arguments' names and
                and their values.
        validators: contains arguments names' and their corresponding
                    validation functions.

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


def validate_categories_dict_schema(x) -> None:
    if not isinstance(x, Mapping):
        raise TypeError(
            (
                "categories must be stored in a mapping"
                f" not {type(x).__name__}"
            )
        )
    try:
        keys = list(key for key in x)
        expect_type(list)(*keys)
        values = list(x[key] for key in x)
        expect_type(list)(*values)
    except TypeError as e:
        raise TypeError("categories have invalid mapping structure") from e


def validate_shipment_dict_schema(x) -> None:
    if not isinstance(x, Sequence):
        raise TypeError(
            f"rules must be stored in a sequence not {type(x).__name__}"
        )
    try:
        expect_type(Mapping)(*x)
    except TypeError as e:
        raise TypeError("rules have invalid structure") from e


def validate_rule_dict_schema(x) -> None:
    if not isinstance(x, Sequence):
        raise TypeError(
            (
                "rules must be stored in a sequence not"
                f"in a {type(x).__name__}"
            )
        )
    for e in x:
        if not isinstance(e, Mapping):
            raise TypeError(
                (
                    "rule must be defined as a mapping not"
                    f" {type(x).__name__}"
                )
            )
        if len(e) != 2:
            raise TypeError(
                f"rule must contain exactly two keys not {len(e)} keys"
            )

        if "params" not in e or "name" not in e:
            k = "', '".join(key for key in e)
            raise TypeError(
                (
                    "rule must be a mapping with keys 'params' and"
                    f" 'name', but got mapping with keys '{k}'."
                )
            )
        if not isinstance(e["name"], str):
            raise TypeError(
                f"rule's name must be a string not {type(x).__name__}"
            )
