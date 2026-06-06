import frappe

def update_workspace():
    workspace = frappe.get_doc("Workspace", "Hotels")
    
    links_to_add = [
        {"label": "Room", "link_to": "Room", "link_type": "DocType", "type": "Link"},
        {"label": "Reservation Settings", "link_to": "Reservation Settings", "link_type": "DocType", "type": "Link"},
        {"label": "Reports", "type": "Card Break"},
        {"label": "Available Rooms", "link_to": "Available Rooms", "link_type": "Report", "type": "Link"},
        {"label": "Room Financials", "link_to": "Room Financials", "link_type": "Report", "type": "Link"}
    ]
    
    for link_data in links_to_add:
        exists = False
        for link in workspace.links:
            if link.label == link_data.get("label") and link.type == link_data.get("type"):
                exists = True
                break
        
        if not exists:
            workspace.append("links", link_data)
            
    # Also update content field for the layout
    import json
    content = json.loads(workspace.content)
    
    # Check if Reports card exists
    has_reports = False
    for item in content:
        if item.get("type") == "card" and item.get("data", {}).get("card_name") == "Reports":
            has_reports = True
            break
            
    if not has_reports:
        # Generate a unique id for the card
        import string, random
        card_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        content.append({
            "id": card_id,
            "type": "card",
            "data": {
                "card_name": "Reports",
                "col": 4
            }
        })
        workspace.content = json.dumps(content)

    workspace.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace updated successfully.")

if __name__ == "__main__":
    update_workspace()
