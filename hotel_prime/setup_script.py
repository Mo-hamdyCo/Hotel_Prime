import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def create_doctypes():
    frappe.flags.in_test = True # prevent some validations if needed

    # 1. Reservation Settings (Single)
    if not frappe.db.exists("DocType", "Reservation Settings"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Reservation Settings",
            "module": "Hotel Mange",
            "custom": 0,
            "issingle": 1,
            "fields": [
                {"fieldname": "standard_check_in_time", "fieldtype": "Time", "label": "Standard Check-In Time", "description": "Default time for check-in"},
                {"fieldname": "standard_check_out_time", "fieldtype": "Time", "label": "Standard Check-Out Time", "description": "Default time for check-out"},
                {"fieldname": "late_check_out_grace_period", "fieldtype": "Int", "label": "Late Check-Out Grace Period (Mins)", "description": "Minutes allowed past standard checkout before charging"},
                {"fieldname": "default_room_service_warehouse", "fieldtype": "Link", "options": "Warehouse", "label": "Default Room Service Warehouse", "description": "Warehouse from which stock is deducted for services"},
                {"fieldname": "post_check_out_room_status", "fieldtype": "Select", "options": "Dirty\nAvailable\nUnder Disinfection", "label": "Post Check-Out Room Status", "description": "Status set to the room automatically upon check-out"},
                {"fieldname": "cancellation_fee_percentage", "fieldtype": "Percent", "label": "Cancellation Fee Percentage", "description": "Percentage charged if a paid reservation is cancelled"},
                {"fieldname": "cancellation_fee_account", "fieldtype": "Link", "options": "Account", "label": "Cancellation Fee Account", "description": "Income account used for cancellation fees"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1}]
        })
        doc.insert(ignore_permissions=True)
        print("Created Reservation Settings")

    # 2. Room
    if not frappe.db.exists("DocType", "Room"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Room",
            "module": "Hotel Mange",
            "custom": 0,
            "autoname": "field:room_name",
            "fields": [
                {"fieldname": "room_name", "fieldtype": "Data", "label": "Room Name", "reqd": 1, "unique": 1},
                {"fieldname": "item", "fieldtype": "Link", "options": "Item", "label": "Item (Billing)", "reqd": 1},
                {"fieldname": "room_status", "fieldtype": "Select", "options": "Available\nOccupied\nDirty\nUnder Disinfection", "label": "Room Status", "default": "Available"},
                {"fieldname": "floor", "fieldtype": "Data", "label": "Floor"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1}]
        })
        doc.insert(ignore_permissions=True)
        print("Created Room")

    # 3. Room Occupancy Log
    if not frappe.db.exists("DocType", "Room Occupancy Log"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Room Occupancy Log",
            "module": "Hotel Mange",
            "custom": 0,
            "fields": [
                {"fieldname": "room", "fieldtype": "Link", "options": "Room", "label": "Room", "reqd": 1},
                {"fieldname": "reservation", "fieldtype": "Link", "options": "Reservation Room", "label": "Reservation", "reqd": 1},
                {"fieldname": "from_datetime", "fieldtype": "Datetime", "label": "From Datetime", "reqd": 1},
                {"fieldname": "to_datetime", "fieldtype": "Datetime", "label": "To Datetime"},
                {"fieldname": "rate", "fieldtype": "Currency", "label": "Rate"},
                {"fieldname": "status", "fieldtype": "Select", "options": "Active\nCompleted\nCancelled", "label": "Status", "default": "Active"}
            ],
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1}]
        })
        doc.insert(ignore_permissions=True)
        print("Created Room Occupancy Log")

    # 4. Room History (Child Table)
    if not frappe.db.exists("DocType", "Room History"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Room History",
            "module": "Hotel Mange",
            "custom": 0,
            "istable": 1,
            "fields": [
                {"fieldname": "room", "fieldtype": "Link", "options": "Room", "label": "Room", "reqd": 1, "in_list_view": 1},
                {"fieldname": "from_datetime", "fieldtype": "Datetime", "label": "From", "reqd": 1, "in_list_view": 1},
                {"fieldname": "to_datetime", "fieldtype": "Datetime", "label": "To", "in_list_view": 1},
                {"fieldname": "qty", "fieldtype": "Float", "label": "Qty", "default": "1"},
                {"fieldname": "rate", "fieldtype": "Currency", "label": "Rate", "in_list_view": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("Created Room History")

    # 5. Accompanying Person (Child Table)
    if not frappe.db.exists("DocType", "Accompanying Person"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Accompanying Person",
            "module": "Hotel Mange",
            "custom": 0,
            "istable": 1,
            "fields": [
                {"fieldname": "full_name", "fieldtype": "Data", "label": "Full Name", "reqd": 1, "in_list_view": 1},
                {"fieldname": "id_number", "fieldtype": "Data", "label": "National ID / Passport", "in_list_view": 1},
                {"fieldname": "phone", "fieldtype": "Data", "label": "Phone Number", "in_list_view": 1},
                {"fieldname": "relationship", "fieldtype": "Data", "label": "Relationship / Role", "in_list_view": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        print("Created Accompanying Person")

def update_reservation_room():
    if not frappe.db.exists("DocType", "Reservation Room"):
        print("Reservation Room not found, skipping update")
        return

    doc = frappe.get_doc("DocType", "Reservation Room")

    # We need to add or update fields
    existing_fields = {f.fieldname: f for f in doc.fields}

    def add_or_update(field_def, insert_after=None):
        if field_def["fieldname"] in existing_fields:
            # Update
            f = existing_fields[field_def["fieldname"]]
            for k, v in field_def.items():
                f.set(k, v)
        else:
            # Insert at right place
            idx = len(doc.fields)
            if insert_after and insert_after in existing_fields:
                idx = doc.fields.index(existing_fields[insert_after]) + 1
            
            new_field = doc.append("fields", field_def)
            # Move to idx
            doc.fields.remove(new_field)
            doc.fields.insert(idx, new_field)

    # Convert dates to datetimes
    add_or_update({"fieldname": "check_in", "fieldtype": "Datetime", "label": "Check In", "reqd": 1})
    add_or_update({"fieldname": "expected_check_out", "fieldtype": "Datetime", "label": "Expected Check Out", "reqd": 1})

    # Add actual dates and hourly flag
    add_or_update({"fieldname": "is_hourly", "fieldtype": "Check", "label": "Is Hourly", "default": "0"}, insert_after="check_in")
    add_or_update({"fieldname": "actual_check_in_datetime", "fieldtype": "Datetime", "label": "Actual Check In", "read_only": 1}, insert_after="check_in")
    add_or_update({"fieldname": "actual_check_out_datetime", "fieldtype": "Datetime", "label": "Actual Check Out", "read_only": 1}, insert_after="expected_check_out")

    # Change Room to Link to Room instead of Item
    add_or_update({"fieldname": "room", "fieldtype": "Link", "options": "Room", "label": "Room", "link_filters": "[]", "mandatory_depends_on": "eval:doc.type_of_reservation=='Single Room'"})

    # Add Sales Invoice link
    add_or_update({"fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "label": "Sales Invoice", "read_only": 1}, insert_after="reservation_status")

    # Update Status options
    add_or_update({
        "fieldname": "reservation_status", 
        "fieldtype": "Select", 
        "label": "Reservation Status",
        "options": "Booked\nChecked-in\nPending Billing\nCompleted\nCancelled\nNo-Show",
        "read_only": 1,
        "default": "Booked"
    })

    # Add Child Tables
    add_or_update({"fieldname": "room_history", "fieldtype": "Table", "options": "Room History", "label": "Room History"}, insert_after="room_details_section")
    add_or_update({"fieldname": "accompanying_persons", "fieldtype": "Table", "options": "Accompanying Person", "label": "Accompanying Persons"}, insert_after="room_details_section")

    doc.save(ignore_permissions=True)
    print("Updated Reservation Room")

def update_item_doctype():
    if not frappe.db.exists("Custom Field", "Item-custom_room_status"):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Item",
            "fieldname": "custom_room_status",
            "label": "Room Status",
            "fieldtype": "Select",
            "options": "Available\nOccupied\nDirty\nUnder Disinfection",
            "insert_after": "item_group"
        })
        custom_field.insert(ignore_permissions=True)
        print("Added custom_room_status to Item")
    else:
        print("custom_room_status already exists on Item")
