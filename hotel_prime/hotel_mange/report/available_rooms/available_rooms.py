# Copyright (c) 2026, M.Hamdy and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from hotel_prime.hotel_mange.doctype.reservation_room.reservation_room import (
	get_overlapping_reservations_for_room,
	room_is_available_for_window,
)

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Room Name"), "fieldname": "name", "fieldtype": "Link", "options": "Room", "width": 150},
        {"label": _("Floor"), "fieldname": "floor", "fieldtype": "Data", "width": 100},
        {"label": _("Status"), "fieldname": "room_status", "fieldtype": "Data", "width": 120},
        {"label": _("Available From"), "fieldname": "available_from", "fieldtype": "Datetime", "width": 180},
        {"label": _("Current Reservation"), "fieldname": "reservation", "fieldtype": "Link", "options": "Reservation Room", "width": 180}
    ]

def get_data(filters):
    filters = filters or {}
    conditions = ["1=1"]
    params = []
    start_dt = get_datetime(filters.get("from_datetime") or now_datetime())
    end_dt = get_datetime(filters.get("to_datetime") or (start_dt + timedelta(minutes=1)))

    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(minutes=1)

    if filters.get("room_status"):
        conditions.append("room_status = %s")
        params.append(filters.get("room_status"))
    if filters.get("floor"):
        conditions.append("floor = %s")
        params.append(filters.get("floor"))

    rooms = frappe.db.sql(
        f"""
        SELECT name, floor, room_status
        FROM `tabRoom`
        WHERE {' AND '.join(conditions)}
        """,
        tuple(params),
        as_dict=True,
    )

    for r in rooms:
        r["available_from"] = None
        r["reservation"] = None
        if room_is_available_for_window(r.name, start_dt, end_dt):
            r["available_from"] = start_dt
        else:
            overlaps = get_overlapping_reservations_for_room(r.name, start_dt, end_dt)
            if overlaps:
                r["available_from"] = max(row.expected_check_out for row in overlaps)
                r["reservation"] = overlaps[0].name
            elif r.room_status == "Under Maintenance":
                r["reservation"] = _("Under Maintenance")
            elif r.room_status == "Blocked":
                r["reservation"] = _("Blocked")

    return rooms
