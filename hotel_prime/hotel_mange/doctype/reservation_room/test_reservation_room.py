from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from hotel_prime.hotel_mange.doctype.reservation_room.reservation_room import (
	can_checkout,
	calculate_late_checkout_fee,
	can_check_in_now,
	normalize_reservation_window,
	windows_overlap,
)


def test_checkout_is_blocked_when_outstanding_exists():
	reservation = SimpleNamespace(outstanding=10, checkout_override_allowed=False)

	assert can_checkout(reservation) is False


def test_checkout_is_allowed_when_outstanding_is_cleared():
	reservation = SimpleNamespace(outstanding=0, checkout_override_allowed=False)

	assert can_checkout(reservation) is True


def test_normalize_reservation_window_applies_standard_times():
	reservation = SimpleNamespace(
		check_in="2026-06-04",
		expected_check_out="2026-06-05",
		is_hourly=False,
	)

	normalize_reservation_window(reservation, "13:00:00", "12:00:00")

	assert reservation.check_in.hour == 13
	assert reservation.check_in.minute == 0
	assert reservation.expected_check_out.hour == 12
	assert reservation.expected_check_out.minute == 0


def test_windows_overlap_respects_checkout_boundary():
	current_start = datetime(2026, 6, 4, 13, 0)
	current_end = datetime(2026, 6, 5, 12, 0)
	next_start = datetime(2026, 6, 5, 13, 0)
	next_end = datetime(2026, 6, 6, 12, 0)

	assert windows_overlap(current_start, current_end, next_start, next_end) is False


def test_check_in_only_allowed_at_or_after_standard_time():
	reservation_start = datetime(2026, 6, 4, 13, 0)
	now_before = datetime(2026, 6, 4, 12, 30)
	now_after = datetime(2026, 6, 4, 13, 15)

	assert can_check_in_now(now_before, reservation_start) is False
	assert can_check_in_now(now_after, reservation_start) is True


def test_late_checkout_fee_uses_hourly_rate_after_grace_period():
	actual_checkout = datetime(2026, 6, 5, 15, 20)
	scheduled_checkout = datetime(2026, 6, 5, 12, 0)

	fee_hours, fee_amount = calculate_late_checkout_fee(actual_checkout, scheduled_checkout, 30, 100)

	assert fee_hours == 4
	assert fee_amount == 400


def test_late_checkout_fee_is_zero_inside_grace_period():
	actual_checkout = datetime(2026, 6, 5, 12, 20)
	scheduled_checkout = datetime(2026, 6, 5, 12, 0)

	fee_hours, fee_amount = calculate_late_checkout_fee(actual_checkout, scheduled_checkout, 30, 100)

	assert fee_hours == 0
	assert fee_amount == 0
