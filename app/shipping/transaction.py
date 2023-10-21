import dataclasses
import functools
import logging
from decimal import Decimal
from typing import Any, Mapping, Sequence, TypedDict

from app.shipping.cast import CASTERS, cast_args
from app.shipping.dataclasses import (
    DiscountTransaction,
    ShippingPlan,
    Transaction,
)
from app.shipping.helpers import find
from app.shipping.protocols import (
    HasDiscountRecord,
    HasTransaction,
    SupportsDiscountCalculate,
    SupportsDiscountCorrection,
)
from app.shipping.schemaexec import (
    RuleSchemaDict,
    init_discount_rules_from_schema,
    init_shipping_plans_from_schema,
)
from app.shipping.validate import get_validators, validate_args

from .rules import RegisterDiscountCorrectionRule, RegisterDiscountRule

logger = logging.getLogger(__name__)


class TransactionInput(TypedDict):
    date: str
    carrier: str
    package_size: str


class ShippingPrice(TypedDict):
    reduced_price: Decimal
    applied_discount: Decimal | None


class TransactionProcessor:
    """Determines if discount is applicable and shipping's final price"""

    _transaction_keys = ["date", "carrier", "package_size"]

    def __init__(
        self,
        rules_schemas: Sequence[RuleSchemaDict],
        rule_correction_schema: Sequence[RuleSchemaDict],
        shipment_plans: Sequence[Mapping[str, Any]],
        categories: Mapping[str, Sequence[str]],
    ):
        self._cast_args = functools.partial(cast_args, casters=CASTERS)
        self._validators = functools.partial(
            validate_args, validators=get_validators(categories)
        )
        map_discount_rules: Mapping[str, SupportsDiscountCalculate]
        map_discount_rules = init_discount_rules_from_schema(
            RegisterDiscountRule.get_rules(),
            rules_schemas,
            self._cast_args,
            self._validators,
        )
        self._discount_rules = list(map_discount_rules.values())

        map_correction_rules: Mapping[str, SupportsDiscountCorrection]
        map_correction_rules = init_discount_rules_from_schema(
            RegisterDiscountCorrectionRule.get_rules(),
            rule_correction_schema,
            self._cast_args,
            self._validators,
        )
        self._correction_rules = list(map_correction_rules.values())
        self._shipping_plans = init_shipping_plans_from_schema(
            ShippingPlan, shipment_plans, self._cast_args, self._validators
        )

        self._history: list[HasDiscountRecord] = []

    def _get_lowest_discount(
        self, transaction: HasTransaction, history: Sequence[HasDiscountRecord]
    ) -> Decimal:
        discounts: list[Decimal] = []
        for i, rule in enumerate(self._discount_rules):
            size = rule.calculate_discount(
                transaction, self._shipping_plans, history
            )

            if size is not None and size > 0:
                for correction_rule in self._correction_rules:
                    size = correction_rule.correct_discount(
                        transaction, size, self._shipping_plans, history
                    )
                discounts.append(size)

        if len(discounts) == 0:
            return Decimal("0")

        return max(discounts)

    def _validate_and_cast_to_transaction_obj(
        self, transaction: Mapping[str, Any]
    ) -> Transaction:
        if not isinstance(transaction, Mapping):
            TypeError(
                (
                    "Transaction must be a mapping not"
                    f" {type(transaction).__name__}"
                )
            )

        casted_transaction = self._cast_args(transaction)
        logger.debug("Casted transaction data: %s", repr(casted_transaction))

        self._validators(casted_transaction)
        price_before_discount = find(
            x=self._shipping_plans,
            carrier=transaction["carrier"],
            package_size=transaction["package_size"],
        ).price

        transaction_obj = Transaction(
            **casted_transaction, price=price_before_discount
        )
        return transaction_obj

    def process_transaction(
        self, transaction: dict[str, Any]
    ) -> ShippingPrice:
        """Determines discount's size (if applicable) and price after discount.

        Args:
            transaction: mapping containing keys: 'date' (transaction's date),
                        'carrier' (carrier's name) and 'package_size' (
                        package's size). Values for these keys must be a string

        Returns:
            Returns dictionary with keys 'reduce_price' and 'applied_discount'.
            If discount is applicable, 'reduce_price' value
            is a shipping price after discount is applied
            and  'applied_discount' value is a discount size.
            If discount is not applicable, 'reduce_price' value is a
            shipping price and 'applied_discount' value set to None.

        """
        logger.debug("Processing transaction: %s", repr(transaction))

        _transaction = {
            k: v for k, v in transaction.items() if k in self._transaction_keys
        }
        transaction_obj = self._validate_and_cast_to_transaction_obj(
            _transaction
        )

        discount = self._get_lowest_discount(transaction_obj, self._history)

        logging.debug("Calculated lowest discount: %s", discount)

        self._history.append(
            DiscountTransaction(
                discount=discount, **dataclasses.asdict(transaction_obj)
            )
        )

        if discount > Decimal("0"):
            return {
                "reduced_price": transaction_obj.price - discount,
                "applied_discount": discount,
            }
        else:
            return {
                "reduced_price": transaction_obj.price,
                "applied_discount": None,
            }
