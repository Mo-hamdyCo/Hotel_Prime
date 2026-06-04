import frappe

from hotel_prime.hotel_mange.doctype.reservation_room.reservation_room import refresh_reservation_financials


def _get_reservation_names_by_invoice(invoice_name):
	reservations = set()

	for name in frappe.get_all("Reservation Room", filters={"sales_invoice": invoice_name}, pluck="name"):
		reservations.add(name)

	child_rows = frappe.db.sql(
		"""
		SELECT DISTINCT parent
		FROM `tabReservation Unit`
		WHERE sales_invoice = %s
		""",
		(invoice_name,),
		as_list=True,
	)
	for row in child_rows:
		reservations.add(row[0])

	return list(reservations)


def sales_invoice_on_submit(doc, method):
	for reservation_name in _get_reservation_names_by_invoice(doc.name):
		refresh_reservation_financials(reservation_name)
		reservation = frappe.get_doc("Reservation Room", reservation_name)
		if reservation.outstanding <= 0 and reservation.reservation_status == "Pending Billing":
			frappe.db.set_value("Reservation Room", reservation_name, "reservation_status", "Completed")


def sales_invoice_on_cancel(doc, method):
	for reservation_name in _get_reservation_names_by_invoice(doc.name):
		refresh_reservation_financials(reservation_name)
		frappe.db.set_value("Reservation Room", reservation_name, "reservation_status", "Pending Billing")
