// Copyright (c) 2026, M.Hamdy and contributors
// For license information, please see license.txt

frappe.query_reports["Available Rooms"] = {
	"filters": [
        {
            "fieldname": "from_datetime",
            "label": __("From"),
            "fieldtype": "Datetime",
            "width": "120"
        },
        {
            "fieldname": "to_datetime",
            "label": __("To"),
            "fieldtype": "Datetime",
            "width": "120"
        },
        {
            "fieldname": "room_status",
            "label": __("Room Status"),
            "fieldtype": "Select",
            "options": "\nAvailable\nBusy\nUnder Maintenance\nBlocked",
            "width": "80"
        },
        {
            "fieldname": "floor",
            "label": __("Floor"),
            "fieldtype": "Data",
            "width": "80"
        }
	]
};
