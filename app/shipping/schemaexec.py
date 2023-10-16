"""Initializes classes from schemas

This module initializes classes from schemas (=sequences of mappings) in a
secure way: variables that needs to be casted to different class will be
casted and all variables are validated before passing to class' __init__
method.
"""

import logging
from typing import Any, Callable, Mapping, Sequence, TypedDict, TypeVar

from app.shipping.validate import expect_type

T = TypeVar("T")
logger = logging.getLogger(__name__)


class RuleSchemaDict(TypedDict):
    name: str
    params: dict[str, Any]


def init_discount_rules_from_schema(
    rule_cls: Sequence[type[T]],
    rule_schemas: Sequence[RuleSchemaDict],
    caster: Callable[[Any], Mapping],
    validator: Callable[[Any], Any],
) -> Mapping[str, T]:
    validate_rule_dict_schema(rule_schemas)

    objects = {}
    map_cls = {cls.__name__: cls for cls in rule_cls}

    for rule_schema in rule_schemas:
        logger.debug("Executing schema: %s", repr(rule_schema))

        casted_args = caster(rule_schema["params"])
        logger.debug("Casted args: %s", repr(casted_args))

        validator(casted_args)

        if rule_schema["name"] not in map_cls:
            raise ValueError(
                (
                    f"can't initiate rule '{rule_schema['name']}' from"
                    " schema since rule is not provided."
                )
            )

        rule_obj = map_cls[rule_schema["name"]](**casted_args)
        objects.update({rule_schema["name"]: rule_obj})

    return objects


def init_shipping_plans_from_schema(
    shipping_cls: type[T],
    shipping_plans: Sequence[Mapping[str, Any]],
    caster: Callable[[Any], Mapping],
    validator: Callable[[Any], Any],
) -> Sequence[T]:
    validate_shipment_dict_schema(shipping_plans)
    objects = []

    for shipping_plan in shipping_plans:
        casted_args = caster(shipping_plan)
        logger.debug("shipment plan after casting: %s", repr(casted_args))

        validator(casted_args)
        objects.append(shipping_cls(**casted_args))

    return objects


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
            ("rules must be stored in a sequence" f" not {type(x).__name__}")
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
                "rule must be defined as a mapping not {type(x).__name__}"
            )
        if len(e) != 2:
            raise TypeError(
                ("rule must contain exactly two keys not" f" {len(e)} keys")
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
                ("rule's name must be a string not" f" {type(x).__name__}")
            )