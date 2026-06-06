# Copyright (c) 2025, M.Hamdy and contributors
# For license information, please see license.txt

import math
from datetime import time as time_type

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, get_time, getdate, now_datetime, time_diff_in_hours, today
from erpnext.accounts.party import get_party_account
from erpnext.controllers.accounts_controller import (
	get_advance_journal_entries,
	get_advance_payment_entries,
)


STATUS_DRAFT = "Draft"
STATUS_BOOKED = "Booked"
STATUS_CHECKED_IN = "Checked In"
STATUS_PENDING_BILLING = "Pending Billing"
STATUS_COMPLETED = "Completed"
STATUS_CANCELLED = "Cancelled"
STATUS_NO_SHOW = "No Show"

ROOM_STATUS_AVAILABLE = "Available"
ROOM_STATUS_BUSY = "Busy"
ROOM_STATUS_MAINTENANCE = "Under Maintenance"
ROOM_STATUS_BLOCKED = "Blocked"
ACTIVE_BOOKING_STATUSES = (STATUS_BOOKED, STATUS_CHECKED_IN, STATUS_PENDING_BILLING)

@frappe.whitelist()
def get_settings():
	return frappe.get_single("Reservation Settings")


def windows_overlap(start_a, end_a, start_b, end_b):
	return start_a < end_b and end_a > start_b


def normalize_datetime_with_standard_time(value, standard_time):
	dt_value = get_datetime(value) if value else None
	if not dt_value:
		return None

	if standard_time and dt_value.time() == time_type(0, 0, 0):
		standard = get_time(standard_time)
		dt_value = dt_value.replace(
			hour=standard.hour,
			minute=standard.minute,
			second=standard.second,
			microsecond=standard.microsecond,
		)

	return dt_value


def normalize_reservation_window(doc, standard_check_in_time=None, standard_check_out_time=None):
	doc.check_in = normalize_datetime_with_standard_time(doc.check_in, standard_check_in_time)
	doc.expected_check_out = normalize_datetime_with_standard_time(doc.expected_check_out, standard_check_out_time)
	return doc.check_in, doc.expected_check_out


def can_check_in_now(current_datetime, scheduled_check_in):
	return get_datetime(current_datetime) >= get_datetime(scheduled_check_in)


def calculate_late_checkout_fee(actual_checkout, scheduled_checkout, grace_minutes, hourly_rate):
	actual_checkout = get_datetime(actual_checkout)
	scheduled_checkout = get_datetime(scheduled_checkout)

	if actual_checkout <= scheduled_checkout:
		return 0, 0

	delay_seconds = (actual_checkout - scheduled_checkout).total_seconds()
	if delay_seconds <= (flt(grace_minutes) * 60):
		return 0, 0

	delay_hours = math.ceil(delay_seconds / 3600)
	return delay_hours, flt(delay_hours) * flt(hourly_rate)


def get_reservation_units(doc):
	return list(doc.get("reservation_units") or [])


def get_reservation_rooms(doc):
	if get_reservation_units(doc):
		return get_reservation_units(doc)

	if doc.room:
		return [frappe._dict({
			"selection_mode": "Room",
			"room": doc.room,
			"room_type": None,
			"qty": 1,
			"is_hourly": doc.is_hourly,
			"rate": doc.day_rate,
			"amount": 0,
			"sales_invoice": doc.sales_invoice,
			"outstanding": 0,
		})]

	return []


def get_reference_room_name(unit):
	if unit.get("room"):
		return unit.get("room")
	return None


def get_unit_room(unit):
	room_name = unit.get("room")
	if room_name:
		return frappe.get_doc("Room", room_name)
	return None

@frappe.whitelist()
def get_room_rate(customer, room):
	if not customer or not room:
		frappe.throw(_("Customer and room are required."))

	room_item = frappe.db.get_value("Room", room, "item")
	if not room_item:
		frappe.throw(_("The selected room is not linked to an item."))

	price_list = frappe.db.get_value("Customer", customer, "default_price_list")
	if not price_list:
		customer_group = frappe.db.get_value("Customer", customer, "customer_group")
		if customer_group:
			price_list = frappe.db.get_value("Customer Group", customer_group, "default_price_list")

	if not price_list:
		price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")

	if not price_list:
		frappe.throw(_("No default selling price list is configured."))

	item_price = frappe.db.get_value(
		"Item Price",
		{"item_code": room_item, "price_list": price_list},
		"price_list_rate",
	)
	if not item_price:
		frappe.throw(_("No item price found for room item {0} in price list {1}.").format(room_item, price_list))

	return {"price_list": price_list, "day_rate": item_price}


def calculate_unit_amount(doc, unit):
	unit_rate = flt(unit.get("rate"))
	unit_qty = flt(unit.get("qty") or 1)
	is_hourly = bool(unit.get("is_hourly") or doc.is_hourly)

	if is_hourly and doc.check_in and doc.expected_check_out:
		hours = max(1, math.ceil(time_diff_in_hours(doc.expected_check_out, doc.check_in)))
		return unit_rate * unit_qty * hours

	nights = flt(doc.nights or 1)
	return unit_rate * unit_qty * nights


def calculate_totals(doc):
	if doc.check_in and doc.expected_check_out:
		if doc.is_hourly:
			doc.nights = max(1, math.ceil(time_diff_in_hours(doc.expected_check_out, doc.check_in)))
		else:
			doc.nights = (getdate(doc.expected_check_out) - getdate(doc.check_in)).days or 1

	room_units = get_reservation_units(doc)
	if room_units:
		total_room_amount = 0
		for unit in room_units:
			unit.amount = calculate_unit_amount(doc, unit)
			total_room_amount += flt(unit.amount)
	else:
		total_room_amount = flt(doc.day_rate) * flt(doc.nights or 1)

	history_amount = sum(flt(row.rate) * flt(row.qty) for row in doc.get("room_history") or [])
	service_amount = sum(flt(row.service_total_amount) for row in doc.get("other_service") or [])
	expense_amount = sum(flt(row.expenses_rate) for row in doc.get("other_expense") or [])
	guest_charge = flt(doc.extra_guest_charge)
	late_checkout_fee = flt(doc.late_check_out_fee)
	discount_amount = min(
		flt(doc.discount_amount),
		total_room_amount + history_amount + service_amount + expense_amount + guest_charge + late_checkout_fee,
	)

	doc.total_nights_amount = total_room_amount + history_amount
	doc.total_amount = doc.total_nights_amount + service_amount + expense_amount + guest_charge + late_checkout_fee - discount_amount

	total_advances = sum(flt(row.advance_amount) for row in doc.get("advances") or [])
	doc.outstanding = doc.total_amount - total_advances
	doc.settlement_amount = doc.outstanding

	if doc.outstanding < 0:
		doc.payment_status = "OverPaid"
	elif flt(doc.outstanding) == 0 and flt(doc.total_amount) > 0:
		doc.payment_status = "Paid"
	elif total_advances > 0:
		doc.payment_status = "Partial Paid"
	else:
		doc.payment_status = "Not Paid"


def can_checkout(doc_or_dict):
	outstanding = flt(doc_or_dict.get("outstanding") if isinstance(doc_or_dict, dict) else doc_or_dict.outstanding)
	override_allowed = bool(
		doc_or_dict.get("checkout_override_allowed") if isinstance(doc_or_dict, dict) else getattr(doc_or_dict, "checkout_override_allowed", False)
	)
	return outstanding <= 0 or override_allowed


def validate_room_selection(doc):
	for unit in get_reservation_rooms(doc):
		if flt(unit.get("qty") or 1) != 1:
			frappe.throw(_("Each reservation unit must have Qty = 1. Add another row for additional rooms."))

		room_name = unit.get("room")
		if room_name:
			room = frappe.get_doc("Room", room_name)
			if room.room_status in {ROOM_STATUS_MAINTENANCE, ROOM_STATUS_BLOCKED}:
				frappe.throw(
					_("Room {0} is not available because it is {1}.").format(room.name, room.room_status)
				)
			continue

		if unit.get("room_type"):
			room_type = unit.get("room_type")
			available = frappe.db.count(
				"Room",
				{"room_type": room_type},
			)
			if not available:
				frappe.throw(_("No room exists for room type {0}.").format(room_type))


def get_overlapping_reservations_for_room(room_name, start_dt, end_dt, exclude_name=None):
	exclude_name = exclude_name or "New"
	statuses = ", ".join(frappe.db.escape(status) for status in ACTIVE_BOOKING_STATUSES)
	return frappe.db.sql(
		f"""
		SELECT DISTINCT rr.name, rr.check_in, rr.expected_check_out, rr.reservation_status
		FROM `tabReservation Room` rr
		LEFT JOIN `tabReservation Unit` ru ON ru.parent = rr.name
		WHERE rr.docstatus < 2
		AND rr.name != %s
		AND rr.reservation_status IN ({statuses})
		AND (
			rr.room = %s
			OR ru.room = %s
		)
		AND (rr.check_in < %s AND rr.expected_check_out > %s)
		""",
		(exclude_name, room_name, room_name, end_dt, start_dt),
		as_dict=True,
	)


def room_is_available_for_window(room_name, start_dt, end_dt, exclude_name=None):
	room = frappe.db.get_value("Room", room_name, ["room_status"], as_dict=True)
	if not room or room.room_status in {ROOM_STATUS_BLOCKED, ROOM_STATUS_MAINTENANCE}:
		return False

	return not get_overlapping_reservations_for_room(room_name, start_dt, end_dt, exclude_name=exclude_name)


def resolve_unit_room(unit, reservation=None, assign=False):
	room_name = unit.get("room")
	if room_name:
		return frappe.get_doc("Room", room_name)

	room_type = unit.get("room_type")
	if not room_type or not reservation:
		return None

	candidate_rooms = frappe.get_all("Room", filters={"room_type": room_type}, pluck="name")
	for candidate_room in candidate_rooms:
		if room_is_available_for_window(
			candidate_room,
			reservation.check_in,
			reservation.expected_check_out,
			exclude_name=reservation.name,
		):
			if assign:
				unit.room = candidate_room
			return frappe.get_doc("Room", candidate_room)

	return None


def validate_room_overlap(doc):
	for unit in get_reservation_rooms(doc):
		if not doc.check_in or not doc.expected_check_out:
			continue

		room_name = unit.get("room")
		if room_name:
			if not room_is_available_for_window(room_name, doc.check_in, doc.expected_check_out, exclude_name=doc.name):
				frappe.throw(
					_("Room {0} is already reserved during the selected time window.").format(room_name)
				)
			continue

		if unit.get("room_type"):
			room_type = unit.get("room_type")
			available_rooms = frappe.get_all("Room", filters={"room_type": room_type}, pluck="name")
			free_rooms = [
				room_name
				for room_name in available_rooms
				if room_is_available_for_window(room_name, doc.check_in, doc.expected_check_out, exclude_name=doc.name)
			]
			if len(free_rooms) < flt(unit.get("qty") or 1):
				frappe.throw(
					_("Not enough rooms of type {0} are available during the selected time window.").format(room_type)
				)


def validate_booking_policy(doc):
	settings = get_settings()
	if settings.advance_required and doc.reservation_status == STATUS_BOOKED:
		total_advances = sum(flt(row.advance_amount) for row in doc.get("advances") or [])
		if total_advances <= 0:
			allowed_role = settings.advance_required_role
			if not allowed_role or allowed_role not in frappe.get_roles():
				frappe.throw(_("An advance payment is required before booking this reservation."))

	if flt(settings.max_discount_percent) and flt(doc.total_amount) > 0:
		max_discount = (flt(settings.max_discount_percent) / 100.0) * flt(doc.total_amount)
		if flt(doc.discount_amount) > max_discount:
			frappe.throw(
				_("Discount cannot exceed the configured maximum of {0}%.").format(settings.max_discount_percent)
			)


def apply_late_checkout_fee(doc, actual_checkout):
	settings = get_settings()
	if not doc.expected_check_out:
		doc.late_check_out_hours = 0
		doc.late_check_out_fee = 0
		return 0, 0

	hourly_rate = flt(settings.late_check_out_hourly_rate)
	fee_hours, fee_amount = calculate_late_checkout_fee(
		actual_checkout,
		doc.expected_check_out,
		settings.late_check_out_grace_period,
		hourly_rate,
	)
	doc.late_check_out_hours = fee_hours
	doc.late_check_out_fee = fee_amount
	return fee_hours, fee_amount


class ReservationRoom(Document):
	def validate(self):
		self.sync_primary_room()
		settings = get_settings()
		normalize_reservation_window(self, settings.standard_check_in_time, settings.standard_check_out_time)
		self.validate_dates()
		validate_room_selection(self)
		validate_room_overlap(self)
		calculate_totals(self)
		validate_booking_policy(self)

	def sync_primary_room(self):
		if self.room or not self.get("reservation_units"):
			return

		first_unit = self.get("reservation_units")[0]
		if first_unit.get("room"):
			self.room = first_unit.get("room")

	def validate_dates(self):
		if self.check_in and self.expected_check_out and self.check_in >= self.expected_check_out:
			frappe.throw(_("Expected Check-Out must be after Check-In time."))


@frappe.whitelist()
def book_reservation(reservation_name):
	doc = frappe.get_doc("Reservation Room", reservation_name)
	doc.reservation_status = STATUS_BOOKED
	calculate_totals(doc)
	validate_booking_policy(doc)
	doc.save()
	return {"status": "success", "message": _("Reservation booked successfully.")}


@frappe.whitelist()
def check_in(reservation_name):
	doc = frappe.get_doc("Reservation Room", reservation_name)

	if doc.reservation_status != STATUS_BOOKED:
		frappe.throw(_("Reservation must be in 'Booked' status to check in."))

	calculate_totals(doc)
	current_time = now_datetime()
	if not can_check_in_now(current_time, doc.check_in):
		frappe.throw(_("Check-In is only allowed at or after {0}.").format(doc.check_in))
	doc.reservation_status = STATUS_CHECKED_IN
	doc.actual_check_in_datetime = current_time
	doc.save()

	for unit in get_reservation_rooms(doc):
		room = resolve_unit_room(unit, reservation=doc, assign=True)
		if not room:
			frappe.throw(_("Unable to resolve an available room for one of the reservation units."))

		frappe.db.set_value("Room", room.name, "room_status", ROOM_STATUS_BUSY)
		frappe.get_doc({
			"doctype": "Room Occupancy Log",
			"room": room.name,
			"reservation": doc.name,
			"from_datetime": doc.actual_check_in_datetime,
			"to_datetime": doc.expected_check_out,
			"rate": unit.get("rate") or doc.day_rate,
			"status": "Active",
		}).insert(ignore_permissions=True)

	doc.save(ignore_permissions=True)
	return {"status": "success", "message": _("Checked in successfully.")}


def create_sales_invoice_for_unit(doc, unit):
	room = resolve_unit_room(unit, reservation=doc, assign=False)
	if not room:
		return None

	item_code = frappe.db.get_value("Room", room.name, "item")
	if not item_code:
		return None

	si = frappe.new_doc("Sales Invoice")
	si.customer = doc.hotel_customer
	si.set_posting_time = 1
	si.posting_date = today()
	si.append("items", {
		"item_code": item_code,
		"qty": flt(unit.get("qty") or 1),
		"rate": flt(unit.get("rate") or doc.day_rate),
		"description": _("Room {0} stay from {1} to {2}").format(
			room.name, doc.actual_check_in_datetime, doc.actual_check_out_datetime or doc.expected_check_out
		),
	})

	settings = get_settings()
	si.update_stock = 1
	if settings.default_room_service_warehouse:
		si.set_warehouse = settings.default_room_service_warehouse

	si.insert(ignore_permissions=True)
	unit.sales_invoice = si.name
	unit.outstanding = flt(si.outstanding_amount or 0)
	unit.status = "Invoiced"
	return si


@frappe.whitelist()
def check_out(reservation_name):
	doc = frappe.get_doc("Reservation Room", reservation_name)

	if doc.reservation_status != STATUS_CHECKED_IN:
		frappe.throw(_("Reservation must be 'Checked In' to check out."))

	calculate_totals(doc)
	settings = get_settings()
	doc.checkout_override_allowed = bool(settings.checkout_override_role and settings.checkout_override_role in frappe.get_roles())
	if not can_checkout(doc):
		frappe.throw(_("Outstanding amount must be settled before check-out."))

		actual_checkout = now_datetime()
	apply_late_checkout_fee(doc, actual_checkout)
	calculate_totals(doc)
	doc.reservation_status = STATUS_PENDING_BILLING
	doc.actual_check_out_datetime = actual_checkout

	for log in frappe.get_all("Room Occupancy Log", filters={"reservation": doc.name, "status": "Active"}, fields=["name", "room"]):
		frappe.db.set_value(
			"Room Occupancy Log",
			log.name,
			{"status": "Completed", "to_datetime": doc.actual_check_out_datetime},
		)
		frappe.db.set_value("Room", log.room, "room_status", settings.maintenance_status_label or ROOM_STATUS_MAINTENANCE)

	created_invoices = []
	for unit in get_reservation_rooms(doc):
		si = create_sales_invoice_for_unit(doc, unit)
		if si:
			created_invoices.append(si.name)

	if flt(doc.late_check_out_fee) > 0:
		fee_item = settings.late_check_out_fee_item
		if not fee_item:
			frappe.throw(_("Late Check-Out Fee Item must be configured to apply late checkout charges."))
		late_fee_invoice = frappe.new_doc("Sales Invoice")
		late_fee_invoice.customer = doc.hotel_customer
		late_fee_invoice.set_posting_time = 1
		late_fee_invoice.posting_date = today()
		late_fee_invoice.append("items", {
			"item_code": fee_item,
			"qty": 1,
			"rate": flt(doc.late_check_out_fee),
			"description": _("Late check-out fee for reservation {0} ({1} hour(s))").format(
				doc.name, doc.late_check_out_hours
			),
		})
		if settings.default_room_service_warehouse:
			late_fee_invoice.set_warehouse = settings.default_room_service_warehouse
		late_fee_invoice.insert(ignore_permissions=True)
		created_invoices.append(late_fee_invoice.name)

	if created_invoices and not doc.sales_invoice:
		doc.sales_invoice = created_invoices[0]

	doc.save()
	return {"status": "success", "message": _("Checked out successfully. Sales invoices created.")}


@frappe.whitelist()
def transfer_room(reservation_name, new_room, rate):
	doc = frappe.get_doc("Reservation Room", reservation_name)
	if doc.reservation_status != STATUS_CHECKED_IN:
		frappe.throw(_("Can only transfer rooms while checked in."))

	current_time = now_datetime()
	for log in frappe.get_all("Room Occupancy Log", filters={"reservation": doc.name, "status": "Active"}, fields=["name", "room"]):
		frappe.db.set_value(
			"Room Occupancy Log",
			log.name,
			{"status": "Completed", "to_datetime": current_time},
		)
		frappe.db.set_value("Room", log.room, "room_status", ROOM_STATUS_MAINTENANCE)

	doc.append("room_history", {
		"room": doc.room,
		"from_datetime": doc.actual_check_in_datetime,
		"to_datetime": current_time,
		"rate": doc.day_rate,
		"qty": 1,
	})
	doc.room = new_room
	doc.day_rate = rate
	doc.actual_check_in_datetime = current_time
	doc.save()

	frappe.get_doc({
		"doctype": "Room Occupancy Log",
		"room": new_room,
		"reservation": doc.name,
		"from_datetime": current_time,
		"to_datetime": doc.expected_check_out,
		"rate": rate,
		"status": "Active",
	}).insert(ignore_permissions=True)

	frappe.db.set_value("Room", new_room, "room_status", ROOM_STATUS_BUSY)
	return {"status": "success", "message": _("Room transferred successfully.")}


@frappe.whitelist()
def process_cancellation(reservation_name):
	doc = frappe.get_doc("Reservation Room", reservation_name)
	if doc.reservation_status not in (STATUS_BOOKED, STATUS_NO_SHOW):
		frappe.throw(_("Reservation cannot be cancelled in its current state."))

	doc.reservation_status = STATUS_CANCELLED
	calculate_totals(doc)
	doc.save()

	settings = get_settings()
	if flt(settings.cancellation_fee_percentage) and flt(doc.total_amount) > 0:
		fee_amount = (flt(settings.cancellation_fee_percentage) / 100.0) * flt(doc.total_amount)
		fee_item = settings.cancellation_fee_item
		if fee_amount > 0 and fee_item:
			si = frappe.new_doc("Sales Invoice")
			si.customer = doc.hotel_customer
			si.append("items", {
				"item_code": fee_item,
				"item_name": "Cancellation Fee",
				"description": _("Cancellation fee for reservation {0}").format(doc.name),
				"qty": 1,
				"rate": fee_amount,
				"income_account": settings.cancellation_fee_account,
			})
			si.insert(ignore_permissions=True)
			return {"status": "success", "message": _("Cancelled. Fee invoice {0} generated.").format(si.name)}

	return {"status": "success", "message": _("Reservation cancelled successfully.")}


@frappe.whitelist()
def get_advances(reservation_name, customer, hotel_customer):
	if not customer:
		frappe.throw(_("Customer is required"))

	company = frappe.db.get_value("Reservation Room", reservation_name, "company")
	if not company:
		frappe.throw(_("Please select a Company in this Reservation"))

	party_type = "Customer"
	party_account = get_party_account(party_type, hotel_customer, company)

	if party_account is None:
		party_account_list = []
	elif isinstance(party_account, str):
		party_account_list = [party_account]
	elif isinstance(party_account, (list, tuple, set)):
		party_account_list = list(party_account)
	else:
		party_account_list = list(party_account)

	try:
		pe_entries = get_advance_payment_entries(
			party_type=party_type,
			party=hotel_customer,
			party_account=party_account_list,
			order_doctype="Reservation Room",
			order_list=[reservation_name],
		)
	except Exception:
		pe_entries = []

	try:
		jv_entries = get_advance_journal_entries(
			party=hotel_customer,
			party_type=party_type,
			party_account=party_account_list,
			amount_field="credit_in_account_currency",
			order_doctype="Reservation Room",
			order_list=[reservation_name],
		)
	except Exception:
		jv_entries = []

	return (pe_entries or []) + (jv_entries or [])


@frappe.whitelist()
def refresh_reservation_financials(reservation_name):
	doc = frappe.get_doc("Reservation Room", reservation_name)
	calculate_totals(doc)

	for unit in get_reservation_rooms(doc):
		if unit.get("sales_invoice"):
			unit.outstanding = flt(frappe.db.get_value("Sales Invoice", unit.get("sales_invoice"), "outstanding_amount") or 0)
			unit.status = "Paid" if flt(unit.outstanding) <= 0 else "Invoiced"

	doc.flags.ignore_validate = True
	doc.save(ignore_permissions=True)
	return {"status": "success", "message": _("Reservation financials refreshed.")}
