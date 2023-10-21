"""Contains discount rules implementations.

There are two groups of discount rules:
* group "discount rules" that determines discount size based on transaction
  details and previous purchase transactions;
* group "discount correction rules" that may alter calculated discount size
  that comes from the first group (in other words, contains rules
  implementation designed for controlling discount size).
"""
import logging
from decimal import Decimal
from typing import Any, Sequence

from app.shipping.helpers import (
    attributes_equal,
    filter_objects,
    mapping_to_pretty_str,
)
from app.shipping.logging import add_trace_logging_level_if_not_exists
from app.shipping.protocols import (
    HasDiscountRecord,
    HasShippingPlan,
    HasTransaction,
    SupportsDiscountCalculate,
    SupportsDiscountCorrection,
)

RULE_NOT_APPLIED = "Rule is not applied:"

add_trace_logging_level_if_not_exists()


logger = logging.getLogger(__name__)


class RegisterDiscountRule:
    """Register discount rule

    Subclasses are included to the list of discount rules. In other words,
    any class that takes this class as a parent class is automatically
    included to available for use discount rule list.
    """

    _rules: list[type[SupportsDiscountCalculate]] = []

    @classmethod
    def get_rules(cls) -> Sequence[type[SupportsDiscountCalculate]]:
        """Get list of registered discount rules"""
        return cls._rules

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not isinstance(cls, SupportsDiscountCalculate):
            raise TypeError(
                f"class {cls.__name__} must support SupportsDiscountCalculate"
                " protocol to be included in discount correction rules"
            )
        cls._rules.append(cls)
        logger.info("Registered discount rule: %s", cls.__name__)


class RegisterDiscountCorrectionRule:
    """Register discount rule

    Subclasses are included to the list of discount correction rules. In
    other words, any class that takes this class as a parent class
    is automatically included to available for use discount correction
    rule list.
    """

    _rules: list[type[SupportsDiscountCorrection]] = []

    @classmethod
    def get_rules(cls) -> Sequence[type[SupportsDiscountCorrection]]:
        """Get list of registered discount correction rules"""
        return cls._rules

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not isinstance(cls, SupportsDiscountCorrection):
            raise TypeError(
                f"class {cls.__name__} must support SupportsDiscountCorrection"
                f" protocol to be included in discount correction rules"
            )
        cls._rules.append(cls)
        logger.info("Registered discount correction rule: %s", cls.__name__)


class MatchLowestPackagePrice(SupportsDiscountCalculate, RegisterDiscountRule):
    """Apply discount by applying lowest shipping price among specific
    package size"""

    def __init__(self, **kwargs: Any):
        """Initializes class instance based on provided parameters

        Args:
            **kwargs: transaction features for determining transaction
                      eligibility for the discount
        """
        self._transaction_type = kwargs
        self._logger = logging.getLogger(f"{__name__}.{self.__str__()}")
        self._logger.info("Initiated class: %s", repr(self))

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            mapping_to_pretty_str(self._transaction_type, value_repr=False),
        )

    def __str__(self):
        return "{}({})".format(
            self.__class__.__name__,
            mapping_to_pretty_str(self._transaction_type, value_repr=True),
        )

    def calculate_discount(
        self,
        transaction: HasTransaction,
        shipping_plans: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        if not attributes_equal(transaction, **self._transaction_type):
            return Decimal("0")

        shipping_plans = list(shipping_plans)
        match_shipping_plan = filter_objects(
            shipping_plans, **self._transaction_type
        )

        match_shipping_plan = sorted(
            match_shipping_plan, key=lambda x: x.price
        )
        discount = transaction.price - match_shipping_plan[0].price

        return discount


class EveryNShipmentIsFreeXTimesInAMonth(
    SupportsDiscountCalculate, RegisterDiscountRule
):
    """Make every N shipping free at most X times a month"""

    def __init__(self, n: int, x_times: int, **kwargs):
        """Initializes class instance based on provided parameters

        Args:
            n: should discount be applied to every transaction (n=1) or every
               second transaction (n=2), etc.
            x_times: maximum number of time per month shipping can be free
            **kwargs: transaction features for determining transaction
                      eligibility for the discount
        """
        self._n = n
        self._transaction_type = kwargs
        self._x_times = x_times
        self._logger = logging.getLogger(f"{__name__}.{self.__str__()}")
        self._logger.info("Initiated class: %s", repr(self))

    def __repr__(self):
        return "{}(n={},x_times={},{})".format(
            self.__class__.__name__,
            repr(self._n),
            repr(self._x_times),
            mapping_to_pretty_str(self._transaction_type, value_repr=False),
        )

    def __str__(self):
        return "{}(n={},x_times={},{})".format(
            self.__class__.__name__,
            str(self._n),
            str(self._x_times),
            mapping_to_pretty_str(self._transaction_type, value_repr=True),
        )

    def calculate_discount(
        self,
        transaction: HasTransaction,
        shipping_plans: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        if not attributes_equal(transaction, **self._transaction_type):
            return Decimal("0")

        history = list(history)

        similar_transactions = filter_objects(
            history, **self._transaction_type
        )

        number_of_similar = len(similar_transactions) + 1
        if number_of_similar % self._n == 0:
            nt_transaction = similar_transactions[:: self._n]
            del nt_transaction[0]

            applied_this_month = filter_objects(
                nt_transaction,
                date=lambda x: x.month == transaction.date.month,
            )

            if len(applied_this_month) < self._x_times:
                self._logger.trace(  # type: ignore
                    ("Rule met all requirements for a free shipping.")
                )
                return transaction.price
            else:
                self._logger.trace(  # type: ignore
                    (
                        "%s number of times rule is applied this month"
                        " (%d times) is not less than allowed number of times"
                        " (%d times)."
                    ),
                    RULE_NOT_APPLIED,
                    len(applied_this_month),
                    self._x_times,
                )
        else:
            self._logger.trace(  # type: ignore
                (
                    "%s discount is apply on every %d transaction, but this "
                    "transaction is %d transaction"
                ),
                RULE_NOT_APPLIED,
                self._n,
                number_of_similar,
            )
        return Decimal("0")


class MonthlyAccumulatedDiscountLimiter(
    SupportsDiscountCorrection, RegisterDiscountCorrectionRule
):
    """Enforces hard limit on total discount sum per month.

    If discount exceeds total months discount limit, then the discount is
    reduced to the one that would not exceed month's limit."""

    def __init__(self, limit: Decimal):
        self._limit = limit
        self._logger = logging.getLogger(f"{__name__}.{self.__str__()}")
        self._logger.info("Initiated class: %s", repr(self))

    def __repr__(self):
        return "{}(limit={})".format(
            self.__class__.__name__, repr(self._limit)
        )

    def __str__(self):
        return "{}(limit={})".format(self.__class__.__name__, str(self._limit))

    def correct_discount(
        self,
        transaction: HasTransaction,
        discount: Decimal,
        shipping_plans: Sequence[HasShippingPlan],
        history: Sequence[HasDiscountRecord],
    ) -> Decimal:
        history = list(history)

        if discount == 0:
            return Decimal("0")

        month_transactions = filter_objects(
            history, date=lambda x: x.month == transaction.date.month
        )
        month_discounts = sum(t.discount for t in month_transactions)

        exceeds = month_discounts + discount - self._limit
        if exceeds > 0:
            discount -= exceeds
            self._logger.debug("Discount reduced by %s", exceeds)
        return discount
