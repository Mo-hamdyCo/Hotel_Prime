from __future__ import annotations

import json
from pathlib import Path


def test_reservation_settings_has_finance_and_policy_switches():
	meta = json.loads(Path(__file__).with_name("reservation_settings.json").read_text(encoding="utf-8"))
	fields = {field["fieldname"]: field for field in meta["fields"]}

	assert "advance_required" in fields
	assert "advance_required_role" in fields
	assert "checkout_override_role" in fields
	assert "max_discount_percent" in fields
	assert "allow_hourly_booking" in fields
	assert "cancellation_fee_item" in fields
	assert "late_check_out_hourly_rate" in fields
	assert "late_check_out_fee_item" in fields
	assert "blocked_status_label" in fields
