import copy
import json
import logging
from typing import (
    Any,
    Callable,
    Mapping,
    MutableSequence,
    Sequence,
    TypeVar,
)

T = TypeVar("T")
AnyMutableSequence = TypeVar("AnyMutableSequence", bound=MutableSequence)
JSONType = (
    None | int | float | str | bool | list["JSONType"] | dict[str, "JSONType"]
)

logger = logging.getLogger(__name__)


def find(x: Sequence[T], **kwargs: Any) -> T:
    """Find an element from a sequence that meets all search conditions.

    Args:
      x: a sequence of objects.
      **kwargs: search parameters: key is matched to object's attribute's name
              and value is matched to object's attribute's value.
    Returns:
      Returns first object in a sequence that meets search parameters.

    Raises:
      LookupError: if object is not found.
    """
    if len(kwargs) == 0:
        raise TypeError(
            "unable to find object since not a single "
            " search parameter was provided."
        )
    for element in x:
        found = True
        for search_name in kwargs:
            search_value = kwargs[search_name]
            if (
                not hasattr(element, search_name)
                or getattr(element, search_name) != search_value
            ):
                found = False
                break
        if found:
            return element

    text_params = ", ".join(
        f"{key}=={value!s}" for key, value in kwargs.items()
    )
    raise LookupError(
        (
            "unable to find element using provided search parameters:"
            f"{text_params}."
        )
    )


def filter_objects(
    x: AnyMutableSequence, **kwargs: Callable[[Any], bool] | Any
) -> AnyMutableSequence:
    """Get subset of sequence of objects that meets all conditions.

    Args:
        x: a sequence of objects.
        **kwargs: search parameters: names corresponds to sequence's object's
                attribute's names and values are expected sequence's
                object's attribute's values. If provided value is a callable
                then callable is called with passing object's attribute as an
                argument (callable is responsible for determining on whether
                attribute meets conditions)
    Returns:
        Returns shallow copy of provided mutable sequence with objects that
        contains attribute values equal to provided values or, in case of
        callables, whenever callables returned True on an object.
    Raises:
        TypeError: if not a single search parameter is provided.
    """
    y = copy.copy(x)
    if len(kwargs) == 0:
        raise TypeError(
            (
                "unable to filter the sequence since not a single"
                " search parameter was provided."
            )
        )
    for i, element in reversed(list(enumerate(x))):
        for search_name in kwargs:
            search_value = kwargs[search_name]
            value = getattr(element, search_name)
            if isinstance(search_value, Callable):
                if not search_value(value):
                    del y[i]
                    break
            elif value != search_value:
                del y[i]
                break

    return y


def attributes_equal(x: Any, **kwargs: Any) -> bool:
    """Check if object's attributes have expected values

    Args:
        x: object
        **kwargs: names corresponds to object's attribute's names and
                  values are expected object's attribute's values.
    Raises:
        TypeError: if not a single pair of expected attribute name and value is
                   provided.
    Returns:
        bool: returns True if object attributes contains expected values.
              Otherwise, False is returned.
    """
    if len(kwargs) == 0:
        raise TypeError(
            (
                "unable to determine if object attributes have expected"
                " values since not a single pair of attribute name and"
                " expected attribute value was passed"
            )
        )
    for search_name in kwargs:
        search_value = kwargs[search_name]
        if getattr(x, search_name) != search_value:
            return False
    return True


def load_data(file: str) -> JSONType:
    with open(file) as f:
        conf = json.load(f)
    return conf


def mapping_to_pretty_str(
    x: Mapping[Any, Any], *, key_repr: bool = False, value_repr: bool = False
) -> str:
    """Returns string representation of a mapping"""
    display_value = repr if value_repr else str
    display_key = repr if key_repr else str
    return ",".join(f"{display_key(k)}={display_value(x[k])}" for k in x)
