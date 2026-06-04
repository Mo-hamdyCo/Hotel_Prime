import frappe

def create_reports():
    if not frappe.db.exists("Report", "Available Rooms"):
        doc = frappe.get_doc({
            "doctype": "Report",
            "name": "Available Rooms",
            "ref_doctype": "Room",
            "report_name": "Available Rooms",
            "report_type": "Script Report",
            "is_standard": "Yes",
            "module": "Hotel Mange"
        })
        doc.insert(ignore_permissions=True)
        print("Created Available Rooms Report")

    if not frappe.db.exists("Report", "Room Financials"):
        doc = frappe.get_doc({
            "doctype": "Report",
            "name": "Room Financials",
            "ref_doctype": "Reservation Room",
            "report_name": "Room Financials",
            "report_type": "Script Report",
            "is_standard": "Yes",
            "module": "Hotel Mange"
        })
        doc.insert(ignore_permissions=True)
        print("Created Room Financials Report")
