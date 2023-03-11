# Copyright (c) 2023, aazaqout and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ToWhomItConcerns(Document):
    @frappe.whitelist()
    def get_employee_details(self):
        employee_name, department, date_of_joining = frappe.db.get_value(
            "Employee",
            {"name": self.employee},
            ["employee_name", "department", "date_of_joining"],
        )
        salary = get_last_salary_slip(self.employee)
        return {
            "employee_name": employee_name,
            "department": department,
            "date_of_joining": date_of_joining,
            "salary": salary,
        }


def get_last_salary_slip(employee):
    salary_slips = frappe.get_list(
        "Salary Slip",
        filters={"employee": employee, "docstatus": 1},
        fields=["*"],
        order_by="start_date desc",
    )
    if not salary_slips:
        return 0
    return salary_slips[0].net_pay
