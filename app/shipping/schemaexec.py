"""Initializes classes from schemas

Initializes classes from schemas (=sequences of mappings) in a safe way:
variables that needs to be casted to different class will be casted and all
variables are validated before passing to class' __init__ method.
"""

import logging
from typing import Any, Iterable, Mapping, TypeVar

from pydantic import TypeAdapter, validate_call

from app.shipping.pydantic_models import RuleModel

T = TypeVar("T")
logger = logging.getLogger(__name__)


@validate_call
def init_discount_rules_from_schema(
    rule_cls: Iterable[type[T]],
    rule_schemas: Iterable[RuleModel],
    types: Mapping[str, Any],
) -> Mapping[str, T]:
    """Initiate discount rule classes from schema

    Args:
        rule_cls: discount rule classes
        rule_schemas: discount rules schema
        types: discount rules' parameter types

    Raises:
        TypeError: if discount rule does not exists or if parameter type
                  does not not exists for specific rule parameter (__init__
                  method argument)

    Returns:
        Returns mapping of classes' names to their objects
    """
    objects = {}
    map_cls = {cls.__name__: cls for cls in rule_cls}

    for rule_schema in rule_schemas:
        logger.debug("Executing schema: %s", repr(rule_schema))
        if rule_schema.name not in map_cls:
            raise TypeError(
                (
                    f"can't initiate rule '{rule_schema.name}' from schema"
                    " since there is no rule class with this name"
                    " in provided list"
                )
            )

        converted_params = {}
        params = rule_schema.params
        for param_name in params.keys():
            if param_name not in types:
                raise TypeError(
                    f"Missing type for rule parameter {param_name}"
                )
            adapter = TypeAdapter(types[param_name])
            converted_params[param_name] = adapter.validate_python(
                params[param_name]
            )
        rule_obj = map_cls[rule_schema.name](**converted_params)
        objects[rule_schema.name] = rule_obj

    return objects
