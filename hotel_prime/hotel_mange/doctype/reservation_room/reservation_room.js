// Copyright (c) 2025, M.Hamdy and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Reservation Room", {
// 	refresh(frm) {

// 	},
// });
// زر الخروج 
frappe.ui.form.on("Reservation Room", {
    refresh(frm) {
        // يظهر الزر فقط لما تكون الحالة Checked-In
        if (frm.doc.reservation_status === "Checked-In") {
            frm.add_custom_button(
                __("Check-Out"),
                function() {
                    frappe.confirm(
                        "هل أنت متأكد من تنفيذ عملية Check-Out؟",
                        function() {
                            frappe.call({
                                method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.check_out",
                                args: {
                                    reservation_name: frm.doc.name
                                },
                                freeze: true,
                                freeze_message: "جاري تنفيذ عملية Check-Out ...",
                                callback: function(r) {
                                    if (r.message && r.message.status === "success") {
                                        frappe.msgprint("✅ تم تسجيل خروج الغرفة بنجاح.");
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }
            ).addClass("btn-primary");
        }
    }
});



// (الايام) حساب عدد اليالي
frappe.ui.form.on("Reservation Room", {
    check_in: function(frm) {
        calculate_nights(frm);
    },
    expected_check_out: function(frm) {
        calculate_nights(frm);
    }
});

function calculate_nights(frm) {
    if (frm.doc.check_in && frm.doc.expected_check_out) {
        const check_in = frappe.datetime.str_to_obj(frm.doc.check_in);
        const check_out = frappe.datetime.str_to_obj(frm.doc.expected_check_out);
        const diff = frappe.datetime.get_day_diff(check_out, check_in);
        frm.set_value("nights", diff);
    }
}

// التســعيــر بتــاع الــغــرف

frappe.ui.form.on("Reservation Room", {
    hotel_customer(frm) {
        if (frm.doc.hotel_customer && frm.doc.room) {
            frappe.call({
                method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.get_room_rate",
                args: {
                    customer: frm.doc.hotel_customer,
                    room: frm.doc.room
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("price_list", r.message.price_list);
                        frm.set_value("day_rate", r.message.day_rate);
                        frappe.show_alert({ message: __('✅ Room Price Detected Successfully'), indicator: 'orange' });
                    }
                }
            });
        }
    },

    room(frm) {
        if (frm.doc.hotel_customer && frm.doc.room) {
            frappe.call({
                method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.get_room_rate",
                args: {
                    customer: frm.doc.hotel_customer,
                    room: frm.doc.room
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("price_list", r.message.price_list);
                        frm.set_value("day_rate", r.message.day_rate);
                        frappe.show_alert({ message: __('✅ Room Price Detected Successfully'), indicator: 'orange' });
                        //frappe.msgprint(`💰 تم جلب السعر من القائمة: <b>${r.message.price_list}</b>`);
                    }
                }
            });
        }
    }
});


// حســاب اجمالى عدد الايام و سعرها 
frappe.ui.form.on("Reservation Room", {
    day_rate(frm) {
        calculate_total(frm);
    },

    nights(frm) {
        calculate_total(frm);
    }
});

function calculate_total(frm) {
    const day_rate = flt(frm.doc.day_rate);
    const nights = flt(frm.doc.nights);

    if (day_rate && nights) {
        const total = day_rate * nights;
        frm.set_value("total_nights_amount", total);
    } else {
        frm.set_value("total_nights_amount", 0);
    }
}


// تأكيد حجز نفس ميــعاد الخرود 
frappe.ui.form.on("Reservation Room", {
    validate(frm) {
        if (!frm.doc.room || !frm.doc.check_in || !frm.doc.expected_check_out) return;

        frappe.call({
            method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.check_future_conflict",
            args: {
                room: frm.doc.room,
                check_in: frm.doc.check_in,
                expected_check_out: frm.doc.expected_check_out,
                name: frm.doc.name
            },
            async: false,  // عشان التحقق يحصل قبل الحفظ
            callback: function (r) {
                if (!r.message) return;

                if (r.message.status === "overlap") {
                    frappe.throw({
                        title: "❌ Room Already Reserved",
                        message: `This room is already booked during this period (${r.message.reservations.join(", ")}).`
                    });
                }

                if (r.message.status === "same_day") {
                    frappe.confirm(
                        `This reservation starts on the same day another guest is checking out (${r.message.reservations.join(", ")}).<br>Do you want to continue?`,
                        () => {
                            // ✅ يسمح بالحفظ
                            frm.save();
                        },
                        () => {
                            // ❌ يوقف الحفظ
                            frappe.validated = false;
                        }
                    );
                }
            },
        });
    }
});



// frappe.ui.form.on('Reservation Room', {
//     refresh(frm) {
//         // 🔹 زر Check-In يظهر فقط في حالة Booked
//         if (frm.doc.reservation_status === "Booked") {
//             frm.add_custom_button(__('Check-In'), function() {
//                 frappe.call({
//                     method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.check_in",
//                     args: { reservation_name: frm.doc.name },
//                     callback: function(r) {
//                         if (!r.exc) {
//                             frm.reload_doc();
//                             frappe.show_alert({ message: __('✅ Room Checked-In Successfully'), indicator: 'green' });
//                         }
//                     }
//                 });
//             });
//         }

//         // 🔹 زر Check-Out يظهر فقط في حالة Checked-In
//         if (frm.doc.reservation_status === "Checked-In") {
//             frm.add_custom_button(__('Check-Out'), function() {
//                 frappe.call({
//                     method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.check_out",
//                     args: { reservation_name: frm.doc.name },
//                     callback: function(r) {
//                         if (!r.exc) {
//                             frm.reload_doc();
//                             frappe.show_alert({ message: __('🏁 Room Checked-Out Successfully'), indicator: 'blue' });
//                         }
//                     }
//                 });
//             });
//         }
//     },

//     // 🔹 عند تغيير الحالة يدويًا (مثل Booked أو Cancelled)
//     reservation_status(frm) {
//         if (["Booked", "Cancelled"].includes(frm.doc.reservation_status)) {
//             frappe.call({
//                 method: "hotel_prime.hotel_mange.doctype.reservation_room.reservation_room.update_room_log_status",
//                 args: {
//                     reservation_name: frm.doc.name,
//                     new_status: frm.doc.reservation_status
//                 },
//                 callback: function(r) {
//                     if (!r.exc) {
//                         frappe.show_alert({
//                             message: __('📘 Room Log Updated to: {0}', [frm.doc.reservation_status]),
//                             indicator: frm.doc.reservation_status === "Cancelled" ? 'red' : 'green'
//                         });
//                     }
//                 }
//             });
//         }
//     }
// });


