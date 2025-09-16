# Server Script: API - create_invoice_from_adjustments
import frappe
from frappe.utils import nowdate, flt

@frappe.whitelist()
def create_invoice_from_adjustments(sales_order_name, submit_invoice=False):
    if not sales_order_name:
        frappe.throw("sales_order_name is required")

    so = frappe.get_doc("Sales Order", sales_order_name)
    items = []
    adj_rows = []
    for a in (so.custom_event_adjustment or []):
        if a.adjustment_type == "Addition" and not a.linked_invoice:
            items.append({
                "item_code": a.item_code or None,
                "description": a.description or "",
                "qty": flt(a.qty or 0),
                "rate": flt(a.rate or 0),
                "amount": flt(a.amount or 0)
            })
            adj_rows.append(a)

    if not items:
        frappe.throw("No un-invoiced additions found")

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": so.customer,
        "posting_date": nowdate(),
        "due_date": nowdate(),
        "items": items,
        "sales_order": so.name
    })
    si.insert()
    if submit_invoice:
        si.submit()

    # link invoice back to adjustments
    for a in adj_rows:
        a.linked_invoice = si.name
    so.save()

    return si.name