# Copyright (c) 2026, M.Hamdy and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Reservation"), "fieldname": "name", "fieldtype": "Link", "options": "Reservation Room", "width": 150},
        {"label": _("Customer"), "fieldname": "hotel_customer", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Status"), "fieldname": "reservation_status", "fieldtype": "Data", "width": 120},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Outstanding"), "fieldname": "outstanding", "fieldtype": "Currency", "width": 140},
        {"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 150}
    ]

def get_data(filters):
    filters = filters or {}
    conditions = ["docstatus < 2"]
    params = []

    if filters.get("customer"):
        conditions.append("hotel_customer = %s")
        params.append(filters.get("customer"))
    if filters.get("reservation_status"):
        conditions.append("reservation_status = %s")
        params.append(filters.get("reservation_status"))

    reservations = frappe.db.sql(
        f"""
        SELECT name, hotel_customer, reservation_status, total_amount, outstanding, sales_invoice
        FROM `tabReservation Room`
        WHERE {' AND '.join(conditions)}
        """,
        tuple(params),
        as_dict=True,
    )

    return reservations
