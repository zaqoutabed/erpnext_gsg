import frappe
from frappe import _


def issue_items_from_stock(doc, method):
    if doc.material_request_type != "Material Issue" or len(
        [item for item in doc.items if item.qty <= 0]
    ) == len(doc.items):
        return
    from erpnext.stock.doctype.material_request.material_request import make_stock_entry

    stock_entry = make_stock_entry(doc.name)
    stock_entry.save(ignore_permissions=True)
    stock_entry.submit()
    frappe.msgprint(
        _("Stock Entry saved {0} successfully for Material Request {1}").format(
            stock_entry.name, doc.name
        ),
        alert=1,
    )
