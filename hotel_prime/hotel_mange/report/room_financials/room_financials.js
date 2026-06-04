// Copyright (c) 2026, M.Hamdy and contributors
// For license information, please see license.txt

frappe.query_reports["Room Financials"] = {
	"filters": [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": "80"
        },
        {
            "fieldname": "reservation_status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nDraft\nBooked\nChecked In\nPending Billing\nCompleted\nCancelled\nNo Show",
            "width": "80"
        }
	]
};
