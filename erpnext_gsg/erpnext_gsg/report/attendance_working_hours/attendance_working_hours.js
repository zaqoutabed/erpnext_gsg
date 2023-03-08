// Copyright (c) 2023, aazaqout and contributors
// For license information, please see license.txt
/* eslint-disable */
function route_to_attendance(val) {
	window.open(`/app/attendance/${val}`);
  }
frappe.query_reports["Attendance Working Hours"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Employee",
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Department",
		},
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		let format_fields = ["attendance_id"];
		
		if (in_list(format_fields, column.fieldname)) {
			console.log(format_fields, column.fieldname);
			value = `<style>.hover-me:hover{cursor: pointer}</style><span class="hover-me" onclick="route_to_attendance('${value}')">${value}</span>`;
		}

		return value;
	}
};
