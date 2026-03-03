from types import SimpleNamespace

from app.modules.orders.models import OrderStatus, PaymentStatus
from app.modules.orders.state_machine import (
    get_allowed_next_states,
    is_valid_transition,
    validate_state_transition,
)


def _order(status: OrderStatus, payment_status: PaymentStatus):
    return SimpleNamespace(status=status, payment_status=payment_status)


def test_lc_states_are_exposed_after_payment_confirmed():
    allowed = get_allowed_next_states(OrderStatus.PAYMENT_CONFIRMED)
    assert allowed == [OrderStatus.LC_REQUESTED, OrderStatus.CANCELLED]


def test_payment_confirmed_to_assigned_to_exporter_is_not_allowed_directly():
    assert not is_valid_transition(OrderStatus.PAYMENT_CONFIRMED, OrderStatus.ASSIGNED_TO_EXPORTER)


def test_lc_requested_transition_requires_completed_payment():
    order = _order(OrderStatus.PAYMENT_CONFIRMED, PaymentStatus.PENDING)
    is_valid, reason = validate_state_transition(order, OrderStatus.LC_REQUESTED, db=None)
    assert not is_valid
    assert "Payment must be completed" in reason


def test_lc_review_retry_flow_is_allowed():
    assert is_valid_transition(OrderStatus.LC_REQUESTED, OrderStatus.LC_REJECTED)
    assert is_valid_transition(OrderStatus.LC_REJECTED, OrderStatus.LC_REQUESTED)
    assert is_valid_transition(OrderStatus.LC_REQUESTED, OrderStatus.LC_APPROVED)
