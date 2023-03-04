import frappe
def create_taxs_account_head():
    account = {
        "account_name": "tax 16%",
        "account_type": "Tax",
        "company": "",
        "disabled": 0,
        "docstatus": 0,
        "doctype": "Account",
        "freeze_account": "No",
        "include_in_gross": 0,
        "inter_company_account": 0,
        "is_group": 0,
        "parent_account": "", # Duties and Taxes
        "report_type": "Balance Sheet",
        "root_type": "Liability",
        "tax_rate": 16.0,
        "account_currency": None,
    }
    for company in frappe.get_list("Company"):
        company = company.name
        account_doc = frappe.db.get_value("Account", filters={"account_name": "tax 16%", "company": company})
        if not account_doc:
            parent_account = frappe.db.get_value(
                    "Account", filters={
                        "account_name": "Duties and Taxes",
                        "company": company,
                        "is_group": 1
                    }
                ) or None
            account_doc = frappe.new_doc("Account")
            account_doc.update(account)
            account_doc.update({
                "parent_account": parent_account,
                "company": company,
            })
            account_doc.flags.ignore_permissions = True
            account_doc.flags.ignore_mandatory = True
            account_doc.save(ignore_permissions=True)
            frappe.db.commit()
            account_doc = account_doc.name
        create_tax_templates("Purchase Taxes and Charges Template", company, account_doc)
        create_tax_templates("Sales Taxes and Charges Template", company, account_doc)
        

def create_tax_templates(doctype, company, account_doc):
    if frappe.db.exists(doctype, {"title" :"{} - Tax 16%".format(company)}):
        return
    tax_template = frappe.new_doc(doctype)
    tax_template.company = company
    tax_template.disabled = 0
    tax_template.is_default = 1
    tax_template.title = "{} - Tax 16%".format(company)
    # tax_template.name = "{} - Tax 16%".format(company)
    tax_template.append("taxes", {
        "account_head": account_doc,
        "add_deduct_tax": "Add",
        "included_in_print_rate": 1,
        "rate": 16.0,
        "description": "Tax 16%",
        "charge_type": "On Net Total",
        "cost_center": "",
    })
    tax_template.flags.ignore_if_duplicate = True
    tax_template.insert(ignore_permissions=True)
    frappe.db.commit()