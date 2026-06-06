// Copyright (c) 2025, M.Hamdy and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reservation Room", {
	refresh(frm) {
		add_action_buttons(frm);
	},

	check_in(frm) {
		recalculate_duration(frm);
		recalculate_room_totals(frm);
	},

	expected_check_out(frm) {
		recalculate_duration(frm);
		recalculate_room_totals(frm);
	},

	is_hourly(frm) {
		recalculate_duration(frm);
		recalculate_room_totals(frm);
	},

	hotel_customer(frm) {
		get_room_rate(frm);
	},

	room(frm) {
		get_room_rate(frm);
	},

	day_rate(frm) {
		recalculate_room_totals(frm);
	},

	nights(frm) {
		recalculate_room_totals(frm);
	},

	extra_guest_count(frm) {
		recalculate_room_totals(frm);
	},

	discount_amount(frm) {
		recalculate_room_totals(frm);
	},

	discount_reason(frm) {
		recalculate_room_totals(frm);
	},

	reservation_units_add(frm) {
		recalculate_room_totals(frm);
	},
});

function add_action_buttons(frm) {
	if (frm.doc.reservation_status === "Draft") {
		frm.add_custom_button(__("Book"), () => {
			frappe.call({
				method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.book_reservation",
				args: { reservation_name: frm.doc.name },
				freeze: true,
				freeze_message: __("Booking reservation..."),
				callback: (r) => {
					if (!r.exc) {
						frappe.msgprint(__("Reservation booked successfully."));
						frm.reload_doc();
					}
				},
			});
		}).addClass("btn-primary");
	}

	if (frm.doc.reservation_status === "Booked") {
		frm.add_custom_button(__("Check In"), () => {
			frappe.confirm(__("Are you sure you want to check in?"), () => {
				frappe.call({
					method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.check_in",
					args: { reservation_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Processing check in..."),
					callback: (r) => {
						if (!r.exc) {
							frappe.msgprint(__("Room checked in successfully."));
							frm.reload_doc();
						}
					},
				});
			});
		}).addClass("btn-primary");
	}

	if (frm.doc.reservation_status === "Checked In") {
		frm.add_custom_button(__("Check Out"), () => {
			frappe.confirm(__("Check out will create sales invoices for every room. Continue?"), () => {
				frappe.call({
					method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.check_out",
					args: { reservation_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Processing check out..."),
					callback: (r) => {
						if (!r.exc) {
							frappe.msgprint(__("Room checked out successfully."));
							frm.reload_doc();
						}
					},
				});
			});
		}).addClass("btn-danger");

		frm.add_custom_button(__("Transfer Room"), () => {
			frappe.prompt(
				[
					{
						fieldname: "new_room",
						fieldtype: "Link",
						options: "Room",
						label: __("New Room"),
						reqd: 1,
					},
					{
						fieldname: "rate",
						fieldtype: "Currency",
						label: __("New Rate"),
						reqd: 1,
					},
				],
				(values) => {
					frappe.call({
						method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.transfer_room",
						args: {
							reservation_name: frm.doc.name,
							new_room: values.new_room,
							rate: values.rate,
						},
						freeze: true,
						callback: (r) => {
							if (!r.exc) {
								frappe.msgprint(__("Room transferred successfully."));
								frm.reload_doc();
							}
						},
					});
				},
				__("Transfer Room"),
				__("Transfer")
			);
		});
	}

	if (["Draft", "Booked", "No Show"].includes(frm.doc.reservation_status)) {
		frm.add_custom_button(__("Cancel Reservation"), () => {
			frappe.confirm(__("Are you sure you want to cancel this reservation?"), () => {
				frappe.call({
					method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.process_cancellation",
					args: { reservation_name: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (!r.exc) {
							frappe.msgprint(__("Reservation cancelled successfully."));
							frm.reload_doc();
						}
					},
				});
			});
		});
	}

	frm.add_custom_button(__("Get Advances"), () => {
		if (frm.is_new()) {
			frappe.msgprint(__("Please save the reservation first before fetching advances."));
			return;
		}

		frappe.call({
			method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.get_advances",
			args: {
				reservation_name: frm.doc.name,
				customer: frm.doc.hotel_customer,
				hotel_customer: frm.doc.hotel_customer,
			},
			callback: (r) => {
				if (r.message) {
					frm.clear_table("advances");
					(r.message || []).forEach((d) => {
						const row = frm.add_child("advances");
						row.reference_type = d.reference_type;
						row.reference_name = d.reference_name;
						row.advance_amount = d.amount;
						row.allocated_amount = d.allocated_amount;
					});
					frm.refresh_field("advances");
					recalculate_room_totals(frm);
					frappe.msgprint(__("Advance payments fetched successfully."));
				}
			},
		});
	});
}

function get_room_rate(frm) {
	if (!(frm.doc.hotel_customer && frm.doc.room)) {
		return;
	}

	frappe.call({
		method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.get_room_rate",
		args: {
			customer: frm.doc.hotel_customer,
			room: frm.doc.room,
		},
		callback: (r) => {
			if (r.message) {
				frm.set_value("price_list", r.message.price_list);
				frm.set_value("day_rate", r.message.day_rate);
				recalculate_room_totals(frm);
				frappe.show_alert({
					message: __("Room price detected successfully."),
					indicator: "orange",
				});
			}
		},
	});
}

function recalculate_duration(frm) {
	if (!frm.doc.check_in || !frm.doc.expected_check_out) {
		return;
	}

	const check_in = frappe.datetime.str_to_obj(frm.doc.check_in);
	const check_out = frappe.datetime.str_to_obj(frm.doc.expected_check_out);

	if (frm.doc.is_hourly) {
		const hours = (check_out - check_in) / (1000 * 60 * 60);
		frm.set_value("nights", Math.max(1, Math.ceil(hours)));
	} else {
		const diff = frappe.datetime.get_day_diff(check_out, check_in);
		frm.set_value("nights", diff || 1);
	}
}

function recalculate_room_totals(frm) {
	const nights = flt(frm.doc.nights || 1);
	let room_total = 0;

	if (frm.doc.reservation_units && frm.doc.reservation_units.length) {
		(frm.doc.reservation_units || []).forEach((row) => {
			const qty = flt(row.qty || 1);
			const rate = flt(row.rate || 0);
			const is_hourly = row.is_hourly || frm.doc.is_hourly;
			const multiplier = is_hourly ? nights : nights;
			row.amount = rate * qty * multiplier;
			room_total += flt(row.amount);
		});
	} else {
		room_total = flt(frm.doc.day_rate) * nights;
	}

	const services_total = (frm.doc.other_service || []).reduce((acc, row) => acc + flt(row.service_total_amount), 0);
	const expenses_total = (frm.doc.other_expense || []).reduce((acc, row) => acc + flt(row.expenses_rate), 0);
	const guest_charge = flt(frm.doc.extra_guest_charge);
	const discount = flt(frm.doc.discount_amount);

	frm.set_value("total_nights_amount", room_total);
	frm.set_value("total_amount", room_total + services_total + expenses_total + guest_charge - discount);
	frm.refresh_field("reservation_units");
}
