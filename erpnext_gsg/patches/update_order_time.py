import frappe


def execute():
    from frappe.utils import nowtime

    now = nowtime()
    frappe.db.sql(
        f"""
        UPDATE `tabSales Order`
        SET order_time='{now}'
    """
    )
    frappe.db.commit()
