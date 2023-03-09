// Copyright (c) 2023, aazaqout and contributors
// For license information, please see license.txt

frappe.ui.form.on('To Whom It Concerns', {
	// refresh: function(frm) {

	// }
	employee: function(frm){
		const fields = ["employee_name", "department", "date_of_joining", "salary"]
		if(frm.doc.employee){
			fields.forEach(function(field){
				frm.set_value(field, "");
				frm.refresh_field(field);
			})
			frappe.call({
				method: "get_employee_details",
				doc:frm.doc,
				callback: function(r){
					if(r.message){
						fields.forEach(function(field){
							const value = r.message[field] || "";
							frm.set_value(field, value);
							frm.refresh_field(field);
						})
					}
				},
				freeze: true,
				freeze_message: __("Loading...")
			})
		}else{
			fields.forEach(function(field){
				frm.set_value(field, "");
				frm.refresh_field(field);
			})
		}
	}
});
