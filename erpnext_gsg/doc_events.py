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

def qrcode_as_png(doc, data):
    import os
    from pyqrcode import create as qrcreate
    from frappe.utils import get_url

    folder = "Home/Attachments"
    png_file_name = "{}.png".format(doc.name)
    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": png_file_name,
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "folder": folder,
            "content": png_file_name,
        }
    )
    _file.save()
    frappe.db.commit()
    file_path = os.path.join(frappe.get_site_path("public", "files"), _file.file_name)
    url = qrcreate(data)
    with open(file_path, "wb") as png_file:
        url.png(png_file, scale=8)
    return _file.file_url

def generate_qr_code(doc, method):
    data = f" customer : {doc.customer} , Total : {doc.currency}{doc.total}"
    file_url = qrcode_as_png(doc, data)
    
    doc.db_set("gsg_qrcode", file_url)
    frappe.db.commit() 

def attendance_validate(doc, method):
    if not doc.check_in or not doc.check_out:
        return
    if time_diff_in_seconds(doc.check_out, doc.check_in) < 0:
        frappe.throw("Check-out must be after Check-in")
