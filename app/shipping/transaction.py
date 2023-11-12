import logging
from decimal import Decimal
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Sequence,
    TypedDict,
    TypeVar,
)

from pydantic import TypeAdapter, validate_call

from app.shipping.dataclasses import DiscountTransaction
from app.shipping.helpers import find, get_literals_from_obj_attributes
from app.shipping.protocols import HasDiscountRecord, HasTransaction
from app.shipping.pydantic_helpers import (
    get_alias_to_annotation_map,
    validate_iterable_annotations,
)
from app.shipping.pydantic_models import (
    RuleModel,
    ShippingModel,
    TransactionModel,
)
from app.shipping.pydantic_types import RULE_PARAM_TYPES
from app.shipping.schemaexec import init_discount_rules_from_schema

from .rules import RegisterDiscountCorrectionRule, RegisterDiscountRule

T = TypeVar("T")

logger = logging.getLogger(__name__)


class ShippingPrice(TypedDict):
    reduced_price: Decimal
    applied_discount: Decimal | None


class TransactionProcessor:
    """Determines if discount is applicable, discount size and shipping's
    final price"""

    @validate_call
    def __init__(
        self,
        rules_schemas: Iterable[RuleModel],
        rule_correction_schema: Iterable[RuleModel],
        shipping_plans: Iterable[Mapping[str, Any]],
        categorical_names: Iterable[str],
    ):
        """Initialize object based on provided parameters

        Args:
            rules_schemas: discount rule schemas for initializing discount rule
                           objects (discount rules and theirs __init__ methods'
                           parameters)
            rule_correction_schema: discount correction rule schemas for
                                    initializing discount correction rule
                                    objects (provides discount correction
                                    rules and theirs __init__ methods'
                                    parameters)
            shipping_plans: shipping plans
            categorical_names: shipping plan classes' attribute names that are
                               categorical type
        """
        self._shipping_plans = [
            ShippingModel(**shipping_plan) for shipping_plan in shipping_plans
        ]

        category_map = get_literals_from_obj_attributes(
            self._shipping_plans, categorical_names
        )
        self._category_validators = {
            name: TypeAdapter(literal).validate_python
            for name, literal in category_map.items()
        }

        rule_param_type_map = get_alias_to_annotation_map(RULE_PARAM_TYPES)

        self._rules = _initialize_discount_rules(
            rules_schemas,
            RegisterDiscountRule.get_rules(),
            rule_param_type_map,
            self._category_validators,
        )

        self._correction_rules = _initialize_discount_rules(
            rule_correction_schema,
            RegisterDiscountCorrectionRule.get_rules(),
            rule_param_type_map,
            self._category_validators,
        )

        self._history: list[HasDiscountRecord] = []

    def _get_largest_discount(
        self,
        transaction: HasTransaction,
        price: Decimal,
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        """Out of all applicable discounts for transactions provides one with
        largest discount after discount correction."""
        discounts: list[Decimal] = []
        for rule_name, rule in enumerate(self._rules):
            size = rule.calculate_discount(
                transaction, price, self._shipping_plans, history
            )

            if size is not None and size > 0:
                corrected_size = size
                for correction_rule in self._correction_rules:
                    corrected_size = correction_rule.correct_discount(
                        transaction,
                        corrected_size,
                        self._shipping_plans,
                        history,
                    )
                logging.debug(
                    (
                        "Calculated discount from '%s': %s."
                        " Discount after discount correction: %s"
                    ),
                    rule,
                    size,
                    corrected_size,
                )
                discounts.append(corrected_size)

        if len(discounts) == 0:
            return Decimal("0")

        return max(discounts)

    @validate_call
    def process_transaction(
        self, transaction: Mapping[str, Any]
    ) -> ShippingPrice:
        """Determines discount's size (if applicable) and price after discount.

        Args:
            transaction: mapping containing keys: 'date' (transaction's date),
                        'carrier' (carrier's name) and 'package_size' (
                        package's size). Values for these keys must be a string
                        type.

        Returns:
            Returns dictionary with keys 'reduce_price' and 'applied_discount'.
            If discount is applicable, 'reduce_price' value is a shipping price
            after discount is applied and  'applied_discount' value is a
            discount size. If discount is not applicable, 'reduce_price' value
            is a shipping price and 'applied_discount' is 'None'.
        """
        logger.debug("Processing transaction: %s", repr(transaction))

        transaction_obj = TransactionModel(**transaction)

        validate_iterable_annotations(
            transaction_obj, self._category_validators
        )

        price_before_discount = find(
            x=self._shipping_plans,
            carrier=transaction_obj.carrier,
            package_size=transaction_obj.package_size,
        ).price

        discount = self._get_largest_discount(
            transaction_obj, price_before_discount, self._history
        )

        self._history.append(
            DiscountTransaction(
                discount=discount,
                price=price_before_discount,
                **transaction_obj.model_dump()
            )
        )

        if discount > Decimal("0"):
            return {
                "reduced_price": price_before_discount - discount,
                "applied_discount": discount,
            }
        else:
            return {
                "reduced_price": price_before_discount,
                "applied_discount": None,
            }


def _initialize_shipping_plans(shipment_plans: Iterable[Mapping[str, Any]]):
    shipping_plans = TypeAdapter(list[ShippingModel]).validate_python(
        shipment_plans
    )
    return shipping_plans


def _initialize_discount_rules(
    rules_schemas: Iterable[RuleModel],
    rules_cls: Iterable[type[T]],
    rule_params_types: Mapping[str, Any],
    category_validators: Mapping[str, Callable[[Any], Any]],
) -> Iterable[T]:
    map_discount_rules: Mapping[str, T]
    map_discount_rules = init_discount_rules_from_schema(
        rules_cls, rules_schemas, rule_params_types
    )
    discount_rules = list(map_discount_rules.values())
    for rule in discount_rules:
        validate_iterable_annotations(rule, category_validators)
    return discount_rules
