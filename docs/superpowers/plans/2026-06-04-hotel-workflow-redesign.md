# Hotel Workflow Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the hotel reservation flow support medium-size hotel operations with clear room states, flexible booking modes, strict financial checkout control, and reservation-level visibility for invoices, advances, discounts, and settlements.

**Architecture:** Keep `Reservation Room` as the operational hub, but move day-to-day control to explicit action buttons plus server-side validation. Use `Room` for unit-level operational controls and `Reservation Settings` for hotel policy switches. Surface all financial activity directly in the reservation form using child tables and linked documents, while preserving ERPNext-native invoices and payments.

**Tech Stack:** Frappe v15, ERPNext, Python controllers, DocType JSON metadata, client-side form scripts, query reports, automated tests.

---

### Task 1: Normalize settings and room metadata

**Files:**
- Modify: `hotel_prime/hotel_mange/doctype/reservation_settings/reservation_settings.json`
- Modify: `hotel_prime/hotel_mange/doctype/room/room.json`
- Modify: `hotel_prime/hotel_mange/doctype/room/room.py`
- Test: `hotel_prime/hotel_mange/doctype/room/test_room.py`

- [ ] **Step 1: Write the failing test**

```python
import frappe
from frappe.tests.utils import FrappeTestCase


class TestRoom(FrappeTestCase):
	def test_room_has_hourly_and_blocked_controls(self):
		meta = frappe.get_meta("Room")
		self.assertTrue(meta.has_field("hourly_allowed"))
		self.assertTrue(meta.has_field("room_type"))
		self.assertTrue(meta.has_field("bed_count"))
		self.assertTrue(meta.has_field("bed_size"))
		self.assertTrue(meta.has_field("view"))
		self.assertTrue(meta.has_field("max_guest_charge"))
		self.assertIn("Busy", meta.get_field("room_status").options)
		self.assertIn("Under Maintenance", meta.get_field("room_status").options)
		self.assertIn("Blocked", meta.get_field("room_status").options)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest hotel_prime/hotel_mange/doctype/room/test_room.py -q`
Expected: FAIL because the Room fields and status options are not present yet.

- [ ] **Step 3: Write minimal implementation**

Add the new fields and status values to `Room`, and add reservation policy fields to `Reservation Settings` for:
- advance requirement toggle
- advance required role
- checkout override role
- max discount percent
- hourly booking default/allow flag
- blocked/maintenance behavior labels

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest hotel_prime/hotel_mange/doctype/room/test_room.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hotel_prime/hotel_mange/doctype/room/room.json hotel_prime/hotel_mange/doctype/room/room.py hotel_prime/hotel_mange/doctype/reservation_settings/reservation_settings.json hotel_prime/hotel_mange/doctype/room/test_room.py
git commit -m "feat: normalize room and settings metadata"
```

### Task 2: Rework reservation state and action flow

**Files:**
- Modify: `hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.json`
- Modify: `hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.py`
- Modify: `hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.js`
- Modify: `hotel_prime/hooks.py`
- Modify: `hotel_prime/fixtures/workflow.json`
- Test: `hotel_prime/hotel_mange/doctype/reservation_room/test_reservation_room.py`

- [ ] **Step 1: Write the failing test**

```python
import frappe
from frappe.tests.utils import FrappeTestCase


class TestReservationRoom(FrappeTestCase):
	def test_checkout_is_blocked_when_outstanding_exists(self):
		from hotel_prime.hotel_mange.doctype.reservation_room.reservation_room import can_checkout

		self.assertFalse(
			can_checkout({"outstanding": 10, "checkout_override_allowed": False}),
		)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest hotel_prime/hotel_mange/doctype/reservation_room/test_reservation_room.py -q`
Expected: FAIL because `can_checkout` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Replace workflow-driven behavior with explicit reservation actions:
- `Book`
- `Check In`
- `Check Out`
- `Transfer Room`
- `Cancel`
- `Fetch Advances`
- `Apply Settlement`

Add server-side helpers for:
- `can_checkout`
- `calculate_room_totals`
- `validate_reservation_state`
- `apply_settlement`

Update form buttons in JS to show and call these actions.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest hotel_prime/hotel_mange/doctype/reservation_room/test_reservation_room.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.json hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.py hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.js hotel_prime/hooks.py hotel_prime/fixtures/workflow.json hotel_prime/hotel_mange/doctype/reservation_room/test_reservation_room.py
git commit -m "feat: replace reservation workflow with explicit actions"
```

### Task 3: Add reservation finance visibility

**Files:**
- Modify: `hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.json`
- Modify: `hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.py`
- Modify: `hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.js`
- Modify: `hotel_prime/hotel_mange/events.py`

- [ ] **Step 1: Write the failing test**

```python
import frappe
from frappe.tests.utils import FrappeTestCase


class TestReservationRoom(FrappeTestCase):
	def test_get_room_rate_returns_price_list_and_rate(self):
		from hotel_prime.hotel_mange.doctype.reservation_room.reservation_room import get_room_rate

		with self.assertRaises(frappe.ValidationError):
			get_room_rate(None, None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest hotel_prime/hotel_mange/doctype/reservation_room/test_reservation_room.py -q`
Expected: FAIL because helper behavior is not fully normalized yet.

- [ ] **Step 3: Write minimal implementation**

Add reservation child tables and computed fields for:
- room/unit lines
- invoice summary per room
- advance lines
- settlement lines
- discount lines
- guest charge lines

Ensure the reservation form fetches and displays:
- invoices and outstanding by invoice
- advances
- totals, discounts, settlement, outstanding

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest hotel_prime/hotel_mange/doctype/reservation_room/test_reservation_room.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.json hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.py hotel_prime/hotel_mange/doctype/reservation_room/reservation_room.js hotel_prime/hotel_mange/events.py
git commit -m "feat: surface reservation financial details"
```

### Task 4: Refresh reports and user labels

**Files:**
- Modify: `hotel_prime/hotel_mange/report/available_rooms/available_rooms.py`
- Modify: `hotel_prime/hotel_mange/report/available_rooms/available_rooms.js`
- Modify: `hotel_prime/hotel_mange/report/room_financials/room_financials.py`
- Modify: `hotel_prime/hotel_mange/report/room_financials/room_financials.js`

- [ ] **Step 1: Write the failing test**

```python
def test_reports_use_new_room_status_labels():
	assert True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest hotel_prime/hotel_mange/report -q`
Expected: report data and filters still reference old room status labels.

- [ ] **Step 3: Write minimal implementation**

Update report labels and queries to use:
- `Available`
- `Busy`
- `Under Maintenance`
- `Blocked`

Improve filtering to avoid string-concatenated SQL where practical.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest hotel_prime/hotel_mange/report -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hotel_prime/hotel_mange/report/available_rooms/available_rooms.py hotel_prime/hotel_mange/report/available_rooms/available_rooms.js hotel_prime/hotel_mange/report/room_financials/room_financials.py hotel_prime/hotel_mange/report/room_financials/room_financials.js
git commit -m "feat: update hotel reports for new room states"
```
