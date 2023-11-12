from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic.fields import FieldInfo
from typing_extensions import _AnnotatedAlias

T = TypeVar("T")


def _get_alias_from_annotations(annotation) -> str:
    field_info = next(
        arg for arg in get_args(annotation) if isinstance(arg, FieldInfo)
    )
    if not hasattr(field_info, "alias"):
        raise TypeError(
            f"annotation is missing attribute 'alias': {field_info!r}"
        )
    if field_info.alias is None:
        raise TypeError(
            f"annotation's attribute 'alias' is must not be None"
        )
    return field_info.alias


def get_alias_to_annotation_map(
    annotations: tuple[T, ...]
) -> Mapping[str, T]:
    """Extracts alias from from each annotation and builds mapping of aliases
    to annotations.
    """
    out: dict[str, T] = {}
    for annotation in annotations:
        alias = _get_alias_from_annotations(annotation)
        out[alias] = annotation
    return out


def validate_iterable_annotations(
    obj: Any, validation_map: Mapping[str, Callable[[Any], Any]]
):
    """Validate object's property values that are iterables using the provided
    validation callables.

    Args:
        obj: an object
        validation_map:  object property names mapped to their validation
                         callables.
    """
    for attribute_name, annotation in obj.__class__.__annotations__.items():
        if isinstance(get_origin(annotation), Iterable):
            alias = _get_alias_from_annotations(annotation)
            attr = getattr(obj, attribute_name)
            if alias not in validation_map:
                raise TypeError(
                    (
                        "can't validate iterable since validation is missing"
                        f" for iterable '{alias}'"
                    )
                )
            validation_map[alias](attr)
