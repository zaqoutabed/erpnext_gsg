import frappe
from frappe import _
from frappe.utils import time_diff_in_seconds


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


def generate_qr_code(doc, method):
    import requests

    file_name = f"{doc.name}.png"

    data = f" customer : {doc.customer} , Total : {doc.currency}{doc.total}"
    URL = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={data}"

    r = requests.get(URL, allow_redirects=True)
    r.raise_for_status()
    content = r.content
    _file = frappe.new_doc("File")
    _file.update(
        {
            "file_name": file_name,
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "attached_to_field": "gsg_qr_code",
            "folder": "Home/Attachments",
            "is_private": 0,
            "content": content,
        }
    )
    _file.save(ignore_permissions=True)
    doc.db_set("gsg_qr_code", _file.file_url)


def attendance_validate(doc, method):
    if not doc.check_in or not doc.check_out:
        return
    if time_diff_in_seconds(doc.check_out, doc.check_in) < 0:
        frappe.throw("Check-out must be after Check-in")
