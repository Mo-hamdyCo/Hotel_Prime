# Copyright (c) 2025, M.Hamdy and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.workflow import apply_workflow
from frappe.utils import today
from frappe.utils import getdate
from frappe.utils import cint
from frappe.utils import flt

class ReservationRoom(Document):
    def validate(self):
        """تحقق ذكي من تداخل الحجوزات مع مراعاة الحالة"""
        if not (self.room and self.check_in and self.expected_check_out):
            return  # لو البيانات ناقصة مفيش داعي للفحص

        overlapping = frappe.db.sql("""
            SELECT name, check_in, expected_check_out, reservation_status
            FROM `tabReservation Room`
            WHERE room = %s
            AND name != %s
            AND docstatus < 2
            AND reservation_status NOT IN ('Cancelled', 'Checked-out')
            AND (
                (check_in <= %s AND expected_check_out > %s)
                OR (check_in < %s AND expected_check_out >= %s)
                OR (%s < check_in AND %s > expected_check_out)
            )
        """, (
            self.room,
            self.name or "New Reservation",
            self.expected_check_out, self.check_in,
            self.expected_check_out, self.check_in,
            self.check_in, self.expected_check_out
        ), as_dict=True)

        if overlapping:
            overlap_info = overlapping[0]
            frappe.log_error(
                message=f"Overlap detected with: {overlap_info}",
                title=f"Room Overlap - {overlap_info['name']}"
            )


            # ✅ لو الحجز المتداخل حالته Checked-In أو Booked
            if overlap_info["reservation_status"] in ("Booked", "Checked-In"):
                frappe.throw(
                    _("❌ Cannot book this room: overlaps with {0} "
                    "from {1} to {2} (Status: {3})").format(
                        overlap_info['name'],
                        overlap_info['check_in'],
                        overlap_info['expected_check_out'],
                        overlap_info['reservation_status']
                    )
                )

        # ✅ السماح بالحجز في نفس يوم المغادرة فقط بعد Check-out فعلي
        same_day_overlap = frappe.db.exists(
            "Reservation Room",
            {
                "room": self.room,
                "expected_check_out": self.check_in,
                "reservation_status": "Checked-out"
            }
        )

        # تحقق من تداخل الحجوزات
        overlaps = frappe.db.sql("""
            SELECT name, check_in, expected_check_out, reservation_status
            FROM `tabReservation Room`
            WHERE room = %s
            AND name != %s
            AND docstatus < 2
            AND (
                (check_in <= %s AND expected_check_out > %s)
                OR (check_in < %s AND expected_check_out >= %s)
                OR (%s <= check_in AND %s >= expected_check_out)
            )
        """, (
            self.room,
            self.name,
            self.expected_check_out, self.check_in,
            self.expected_check_out, self.check_in,
            self.check_in, self.expected_check_out
        ), as_dict=True)

        if overlaps:
            frappe.flags.room_overlap = overlaps


   # تأكيد حجز نفس يوم الخروج 
@frappe.whitelist()
def check_reservation_overlap(room, check_in, expected_check_out, name=None):
        overlaps = frappe.db.sql("""
            SELECT name, check_in, expected_check_out
            FROM `tabReservation Room`
            WHERE room = %s
            AND name != %s
            AND docstatus < 2
            AND (
                (check_in <= %s AND expected_check_out > %s)
                OR (check_in < %s AND expected_check_out >= %s)
                OR (%s <= check_in AND %s >= expected_check_out)
            )
        """, (
            room,
            name or "",
            expected_check_out, check_in,
            expected_check_out, check_in,
            check_in, expected_check_out
        ), as_dict=True)

        return overlaps
    
# # تحقق من عدم تكرار الحجز    
#     def validate(self):
#         # 🔹 Log البداية (تقدر تشوفها في logs/web.log)
#         frappe.logger().info(f"Start Validation for room: {self.room}, status: {self.reservation_status}")

#         # 🔹 تحقق فقط لو الحالة حجز أو نزيل داخل الغرفة
#         if self.reservation_status in ["Booked", "Checked-In"]:
#             existing = frappe.db.exists(
#                 "Reservation Room",
#                 {
#                     "room": self.room,
#                     "reservation_status": ["in", ["Booked", "Checked-In"]],
#                     "name": ["!=", self.name],  # عشان ما يشملش نفسه أثناء التعديل
#                 }
#             )

#             frappe.logger().info(f"Checking room: {self.room}, existing: {existing}")

#             if existing:
#                 frappe.throw(" الغرفة دي محجوزة بالفعل أو مشغولة حالياً، يرجى اختيار غرفة أخرى.")

# قــــــــــــديـــــــــــــــــم
#     def get_status(self):
#         return self.reservation_status or "Waiting"            

                
#     def before_save(self):
#         # تحديث status bar بناءً على reservation_status
#         self.set_status_based_on_reservation_status()

#     def set_status_based_on_reservation_status(self):
#         """خلي الحالة اللي بتظهر في الأعلى تساوي حالة الحجز"""
#         self.status = self.reservation_status


# # =========================================================
# # 🔹 دوال مستدعاة من الـ JS
# # =========================================================

# @frappe.whitelist()
# def check_in(reservation_name):
#     """تحويل الحالة إلى Checked-In"""
#     doc = frappe.get_doc("Reservation Room", reservation_name)

#     if doc.reservation_status != "Booked":
#         frappe.throw("لا يمكن تنفيذ Check-In إلا لو كانت الحالة الحالية Booked.")

#     doc.reservation_status = "Checked-In"
#     doc.status = "Checked-In"  # تظهر في الشريط العلوي
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()

#    # frappe.msgprint("✅ تم تسجيل دخول الغرفة (Checked-In) بنجاح")
#     return {"status": "success", "new_status": doc.reservation_status}



@frappe.whitelist()
def check_out(reservation_name):
    """تحويل الحالة إلى Checked-Out وتحديث expected_check_out + nights"""
    doc = frappe.get_doc("Reservation Room", reservation_name)

    # التحقق من الحالة الحالية
    if doc.reservation_status != "Checked-In":
        frappe.throw("❌ لا يمكن تنفيذ Check-Out إلا إذا كانت الحالة الحالية Checked-In.")

    # تحديث الحالة
    new_status = "Checked-out"
    check_out_date = today()

    # ✅ تحديث مباشر في قاعدة البيانات حتى لو المستند Submitted
    frappe.db.set_value("Reservation Room", reservation_name, {
        "reservation_status": new_status,
        "expected_check_out": check_out_date,
    })

    # ✅ حساب عدد الليالي (الفرق بين check_in و expected_check_out)
    if doc.check_in:
        check_in_date = getdate(doc.check_in)
        nights = (getdate(check_out_date) - check_in_date).days or 1
        frappe.db.set_value("Reservation Room", reservation_name, "nights", nights)

    # ✅ إعادة تحميل القيم الجديدة بعد التحديث
    doc.reload()

    # ✅ حساب إجمالي قيمة الإقامة (day_rate * nights)
    if doc.day_rate and nights:
        total_nights_amount = flt(doc.day_rate) * flt(nights)
        frappe.db.set_value("Reservation Room", reservation_name, "total_nights_amount", total_nights_amount)


    # محاولة تطبيق الـ workflow (بعد تحديث القيم)
    try:
        apply_workflow(doc, "Checked-out")
    except Exception as e:
        frappe.log_error(f"Workflow transition failed: {e}", "ReservationRoom Check-Out")

    frappe.db.commit()

    return {
        "status": "success",
        "new_status": new_status,
        "expected_check_out": check_out_date,
    }

# @frappe.whitelist()
# def update_room_log_status(reservation_name, new_status):
#     """تحديث حالة الغرفة من التغيير اليدوي"""
#     doc = frappe.get_doc("Reservation Room", reservation_name)
#     doc.reservation_status = new_status
#     doc.status = new_status
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()
#     return {"status": "success", "new_status": new_status}               

# دالــة تــسعــير الــغــرف
#from frappe.utils import cint



@frappe.whitelist()
def get_room_rate(customer, room):
    """
    جلب سعر الغرفة من قائمة الأسعار بناءً على العميل بنفس منطق فاتورة البيع
    """
    if not customer or not room:
        frappe.throw("العميل أو الغرفة غير محددين.")

    # =====================================
    # 1️⃣ تحديد قائمة الأسعار
    # =====================================
    price_list = frappe.db.get_value("Customer", customer, "default_price_list")

    if not price_list:
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        if customer_group:
            price_list = frappe.db.get_value("Customer Group", customer_group, "default_price_list")

    if not price_list:
        price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")

    if not price_list:
        frappe.throw("لا توجد قائمة أسعار افتراضية محددة في النظام.")

    # =====================================
    # 2️⃣ جلب السعر من Item Price
    # =====================================
    item_price = frappe.db.get_value(
        "Item Price",
        {"item_code": room, "price_list": price_list},
        "price_list_rate"
    )

    if not item_price:
        frappe.throw(f"لا يوجد سعر محدد للغرفة {room} في قائمة الأسعار {price_list}.")

    return {
        "price_list": price_list,
        "day_rate": item_price
    }

