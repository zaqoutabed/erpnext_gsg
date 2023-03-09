# Copyright (c) 2023, aazaqout and contributors
# For license information, please see license.txt

import copy
from collections import OrderedDict

import frappe
from frappe import _, qb
from frappe.query_builder import CustomFunction
from frappe.query_builder.functions import Max
from frappe.utils import date_diff, flt, getdate, time_diff_in_seconds


def execute(filters=None):
    if not filters:
        return [], [], None, []

    validate_filters(filters)

    columns = get_columns(filters)
    conditions = get_conditions(filters)
    data = get_data(conditions, filters)
    so_elapsed_time = get_so_elapsed_time(data)

    if not data:
        return [], [], None, []

    data, chart_data = prepare_data(data, so_elapsed_time, filters)

    return columns, data, None, chart_data


def validate_filters(filters):
    from_date, to_date = filters.get("from_date"), filters.get("to_date")

    if not from_date and to_date:
        frappe.throw(_("From and To Dates are required."))
    elif date_diff(to_date, from_date) < 0:
        frappe.throw(_("To Date cannot be before From Date."))

    from_time, to_time = filters.get("from_time"), filters.get("to_time")
    if not from_time and to_time:
        frappe.throw(_("From and To Times are required."))
    elif time_diff_in_seconds(to_time, from_time) < 0:
        frappe.throw(_("To Time cannot be before From Time."))


def get_conditions(filters):
    conditions = [" 1=1 "]
    if filters.get("from_date") and filters.get("to_date"):
        from_date = filters.get("from_date")
        to_date = filters.get("to_date")
        conditions.append(
            f" so.transaction_date between '{from_date}' and '{to_date}' "
        )

    if filters.get("company"):
        company = filters.get("company")
        conditions.append(f" so.company = '{company}' ")

    if filters.get("from_time") and filters.get("to_time"):
        from_time = filters.get("from_time")
        to_time = filters.get("to_time")
        conditions.append(
            f" DATE_FORMAT(so.order_time, '%T') between '{from_time}' and '{to_time}' "
        )

    if filters.get("sales_order"):
        sales_order = filters.get("sales_order")
        conditions.append(f" so.name in ('{sales_order}') ")

    if filters.get("status"):
        status = filters.get("status")
        conditions.append(f" so.status in ('{status}') ")

    return " AND ".join(conditions)


def get_data(conditions, filters):
    # nosemgrep
    data = frappe.db.sql(
        """
        SELECT
            so.transaction_date as date,
            so.order_time as order_time,
            soi.delivery_date as delivery_date,
            so.name as sales_order,
            so.status, so.customer, soi.item_code,
            DATEDIFF(CURDATE(), soi.delivery_date) as delay_days,
            IF(so.status in ('Completed','To Bill'), 0, (SELECT delay_days)) as delay,
            soi.qty, soi.delivered_qty,
            (soi.qty - soi.delivered_qty) AS pending_qty,
            IFNULL(SUM(sii.qty), 0) as billed_qty,
            soi.base_amount as amount,
            (soi.delivered_qty * soi.base_rate) as delivered_qty_amount,
            (soi.billed_amt * IFNULL(so.conversion_rate, 1)) as billed_amount,
            (soi.base_amount - (soi.billed_amt * IFNULL(so.conversion_rate, 1))) as pending_amount,
            soi.warehouse as warehouse,
            so.company, soi.name,
            soi.description as description
        FROM
            `tabSales Order` so,
            `tabSales Order Item` soi
        LEFT JOIN `tabSales Invoice Item` sii
            ON sii.so_detail = soi.name and sii.docstatus = 1
        WHERE
            soi.parent = so.name
            and so.status not in ('Stopped', 'Closed', 'On Hold')
            and so.docstatus = 1
            and {conditions}
        GROUP BY soi.name
        ORDER BY so.transaction_date ASC, soi.item_code ASC
    """.format(
            conditions=conditions
        ),
        as_dict=1,
    )

    return data


def get_so_elapsed_time(data):
    """
    query SO's elapsed time till latest delivery note
    """
    so_elapsed_time = OrderedDict()
    if data:
        sales_orders = [x.sales_order for x in data]

        so = qb.DocType("Sales Order")
        soi = qb.DocType("Sales Order Item")
        dn = qb.DocType("Delivery Note")
        dni = qb.DocType("Delivery Note Item")

        to_seconds = CustomFunction("TO_SECONDS", ["date"])

        query = (
            qb.from_(so)
            .inner_join(soi)
            .on(soi.parent == so.name)
            .left_join(dni)
            .on(dni.so_detail == soi.name)
            .left_join(dn)
            .on(dni.parent == dn.name)
            .select(
                so.name.as_("sales_order"),
                soi.item_code.as_("so_item_code"),
                (
                    to_seconds(Max(dn.posting_date)) - to_seconds(so.transaction_date)
                ).as_("elapsed_seconds"),
            )
            .where((so.name.isin(sales_orders)) & (dn.docstatus == 1))
            .orderby(so.name, soi.name)
            .groupby(soi.name)
        )
        dn_elapsed_time = query.run(as_dict=True)

        for e in dn_elapsed_time:
            key = (e.sales_order, e.so_item_code)
            so_elapsed_time[key] = e.elapsed_seconds

    return so_elapsed_time


def prepare_data(data, so_elapsed_time, filters):
    completed, pending = 0, 0

    if filters.get("group_by_so"):
        sales_order_map = {}

    for row in data:
        # sum data for chart
        completed += row["billed_amount"]
        pending += row["pending_amount"]

        # prepare data for report view
        row["qty_to_bill"] = flt(row["qty"]) - flt(row["billed_qty"])

        row["delay"] = 0 if row["delay"] and row["delay"] < 0 else row["delay"]

        row["time_taken_to_deliver"] = (
            so_elapsed_time.get((row.sales_order, row.item_code))
            if row["status"] in ("To Bill", "Completed")
            else 0
        )

        if filters.get("group_by_so"):
            so_name = row["sales_order"]

            if not so_name in sales_order_map:
                # create an entry
                row_copy = copy.deepcopy(row)
                sales_order_map[so_name] = row_copy
            else:
                # update existing entry
                so_row = sales_order_map[so_name]
                so_row["required_date"] = max(
                    getdate(so_row["delivery_date"]), getdate(row["delivery_date"])
                )
                so_row["delay"] = min(so_row["delay"], row["delay"])

                # sum numeric columns
                fields = [
                    "qty",
                    "delivered_qty",
                    "pending_qty",
                    "billed_qty",
                    "qty_to_bill",
                    "amount",
                    "delivered_qty_amount",
                    "billed_amount",
                    "pending_amount",
                ]
                for field in fields:
                    so_row[field] = flt(row[field]) + flt(so_row[field])

    chart_data = prepare_chart_data(pending, completed)

    if filters.get("group_by_so"):
        data = []
        for so in sales_order_map:
            data.append(sales_order_map[so])
        return data, chart_data

    return data, chart_data


def prepare_chart_data(pending, completed):
    labels = ["Amount to Bill", "Billed Amount"]

    return {
        "data": {"labels": labels, "datasets": [{"values": [pending, completed]}]},
        "type": "donut",
        "height": 300,
    }


def get_columns(filters):
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 90},
        {
            "label": _("Order Time"),
            "fieldname": "order_time",
            "fieldtype": "Time",
            "width": 90,
        },
        {
            "label": _("Sales Order"),
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 160,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 130,
        },
    ]

    if not filters.get("group_by_so"):
        columns.append(
            {
                "label": _("Item Code"),
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 100,
            }
        )
        columns.append(
            {
                "label": _("Description"),
                "fieldname": "description",
                "fieldtype": "Small Text",
                "width": 100,
            }
        )

    columns.extend(
        [
            {
                "label": _("Qty"),
                "fieldname": "qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Delivered Qty"),
                "fieldname": "delivered_qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Qty to Deliver"),
                "fieldname": "pending_qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Billed Qty"),
                "fieldname": "billed_qty",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Qty to Bill"),
                "fieldname": "qty_to_bill",
                "fieldtype": "Float",
                "width": 80,
                "convertible": "qty",
            },
            {
                "label": _("Amount"),
                "fieldname": "amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Billed Amount"),
                "fieldname": "billed_amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Pending Amount"),
                "fieldname": "pending_amount",
                "fieldtype": "Currency",
                "width": 130,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Amount Delivered"),
                "fieldname": "delivered_qty_amount",
                "fieldtype": "Currency",
                "width": 100,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Delivery Date"),
                "fieldname": "delivery_date",
                "fieldtype": "Date",
                "width": 120,
            },
            {
                "label": _("Delay (in Days)"),
                "fieldname": "delay",
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "label": _("Time Taken to Deliver"),
                "fieldname": "time_taken_to_deliver",
                "fieldtype": "Duration",
                "width": 100,
            },
        ]
    )
    if not filters.get("group_by_so"):
        columns.append(
            {
                "label": _("Warehouse"),
                "fieldname": "warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 100,
            }
        )
    columns.append(
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 100,
        }
    )

    return columns
