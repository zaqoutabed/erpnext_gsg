# Copyright (c) 2023, aazaqout and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class EmployeeExcuseApplication(Document):
    def validate(self):
        # Check if the employee has already excused the application
        if (
            len(
                frappe.get_list(
                    "Employee Excuse Application",
                    filters={
                        "employee": self.employee,
                        "name": ["!=", self.name],
                        "excuse_date": self.excuse_date,
                        "docstatus": 1,
                    },
                )
            )
            > 0
        ):
            frappe.throw("This employee has already excuse application")

        if time_diff_in_hours(self.from_time, self.to_time) > 0:
            frappe.throw("From time should before To time")
        self.hours = time_diff_in_hours(self.to_time, self.from_time)
