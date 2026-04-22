"""Install / migrate hook — ensures the WhatsApp-only role exists on every
deploy so admins can assign it to any user without touching the app code."""

import frappe


ROLE_NAME = "WhatsApp Inbox User"


def after_install():
    _ensure_role()


def after_migrate():
    _ensure_role()


def _ensure_role():
    if frappe.db.exists("Role", ROLE_NAME):
        return
    try:
        frappe.get_doc({
            "doctype": "Role",
            "role_name": ROLE_NAME,
            "desk_access": 1,
            "disabled": 0,
            "home_page": "/app/whatsapp-inbox",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create role {ROLE_NAME}: {e}", "WhatsApp Inbox Install")
