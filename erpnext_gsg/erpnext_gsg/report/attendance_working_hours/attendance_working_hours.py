# Copyright (c) 2023, aazaqout and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff


def execute(filters=None):
    if not filters:
        return [], [], None, []

    validate_filters(filters)

    columns = get_columns()
    conditions = get_conditions(filters)
    data = get_data(conditions)

    if not data:
        return [], []

    return columns, data


def validate_filters(filters):
    from_date, to_date = filters.get("from_date"), filters.get("to_date")
    if not from_date and to_date:
        frappe.throw(_("From and To Dates are required."))
    elif date_diff(to_date, from_date) < 0:
        frappe.throw(_("To Date cannot be before From Date."))


def get_conditions(filters):
    conditions = [" 1=1 "]
    if filters.get("from_date") and filters.get("to_date"):
        from_date = filters.get("from_date")
        to_date = filters.get("to_date")
        conditions.append(f" attendance_date between '{from_date}' and '{to_date}' ")

    if filters.get("company"):
        company = filters.get("company")
        conditions.append(f" company = '{company}' ")

    if filters.get("employee"):
        employee = filters.get("employee")
        conditions.append(f" employee = '{employee}' ")

    if filters.get("department"):
        department = filters.get("department")
        conditions.append(f" department = '{department}' ")

    return " AND ".join(conditions)


def get_data(conditions):
    data = frappe.db.sql(
        """
		SELECT
			attendance_date, employee, employee_name, check_in, check_out, name as attendance_id,
            CASE WHEN IFNULL(check_in, '') <> '' AND IFNULL(check_out, '') <> '' 
            	 THEN  TIMESTAMPDIFF(SECOND, check_in, check_out) / 3600.0
			ELSE '0'
			END AS working_hours
		FROM
			`tabAttendance`
		WHERE
			docstatus = 1
			and {conditions}
	""".format(
            conditions=conditions
        ),
        as_dict=1,
    )

    return data


def get_columns():
    columns = [
        {
            "label": _("Attendance Date"),
            "fieldname": "attendance_date",
            "fieldtype": "Date",
            "width": 90,
        },
        {
            "label": _("Employee"),
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 160,
        },
        {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Check In"),
            "fieldname": "check_in",
            "fieldtype": "Time",
            "width": 130,
        },
        {
            "label": _("Check Out"),
            "fieldname": "check_out",
            "fieldtype": "Time",
            "width": 130,
        },
        {
            "label": _("Working Hours"),
            "fieldname": "working_hours",
            "fieldtype": "Float",
            "width": 130,
        },
        {
            "label": _("Attendance"),
            "fieldname": "attendance_id",
            "fieldtype": "HTML",
            "width": 160,
        },
    ]

    return columns
