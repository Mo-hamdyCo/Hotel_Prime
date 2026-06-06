from __future__ import annotations

import json
from pathlib import Path


def test_room_has_new_operational_fields():
	meta = json.loads(Path(__file__).with_name("room.json").read_text(encoding="utf-8"))
	fields = {field["fieldname"]: field for field in meta["fields"]}

	assert "hourly_allowed" in fields
	assert "room_type" in fields
	assert "bed_count" in fields
	assert "bed_size" in fields
	assert "view" in fields
	assert "max_guest_charge" in fields

	status_options = fields["room_status"]["options"]
	assert "Busy" in status_options
	assert "Under Maintenance" in status_options
	assert "Blocked" in status_options
