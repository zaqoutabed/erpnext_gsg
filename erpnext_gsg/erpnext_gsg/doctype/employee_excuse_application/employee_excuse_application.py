# Copyright (c) 2023, aazaqout and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours, get_first_day, get_last_day


class EmployeeExcuseApplication(Document):
    def validate(self):
        if time_diff_in_hours(self.from_time, self.to_time) > 0:
            frappe.throw("From time should before To time")
        self.hours = time_diff_in_hours(self.to_time, self.from_time)
        self.validate_allowed_hours()

    def on_submit(self):
        self.validate_allowed_hours()

    def validate_allowed_hours(self):
        current_employee_department = frappe.db.get_value(
            "Employee", self.employee, "department"
        )
        if not current_employee_department:
            return
        department_hours = (
            frappe.db.get_value(
                "Department", current_employee_department, "excuse_hours_allowed"
            )
            or 0
        )

        if department_hours == 0:
            return

        month_start = get_first_day(self.excuse_date)
        month_end = get_last_day(self.excuse_date)

        total_hours_in_month = frappe.db.sql(
            f"""
            SELECT IFNULL(sum(hours), 0) as hours FROM `tabEmployee Excuse Application`
            WHERE employee='{self.employee}'
            AND department='{current_employee_department}'
            AND excuse_date BETWEEN '{month_start}' AND '{month_end}'
            AND docstatus = 1
        """,
            as_dict=True,
        )
        total_hours_in_month = (
            total_hours_in_month[0].hours if len(total_hours_in_month) > 0 else 0
        )

        if total_hours_in_month > department_hours:
            frappe.throw(
                f"<b>{total_hours_in_month}</b> hours for employee Employee <b>{self.employee}</b> exceeded allowed hours in department <b>{current_employee_department} {department_hours}</b>"
            )
