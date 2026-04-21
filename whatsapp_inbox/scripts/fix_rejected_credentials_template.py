"""
Replace the rejected `user_credentials_ar-ar` template with a Meta-compliant version.

Meta rejects templates that include passwords inline. The new version sends only a
welcome message with the login link + username, and asks the user to set their
own password via "forgot password". Credentials should go via email.

Usage:
    echo "from whatsapp_inbox.scripts.fix_rejected_credentials_template import run; run()" \\
        | bench --site <your-site> console
"""

import frappe

REJECTED_NAME = "user_credentials_ar-ar"

# Compliant replacement: welcome + login link only, no password sent on WhatsApp
NEW_TEMPLATE = {
    "template_name": "user_welcome_ar",
    "actual_name": "user_welcome_ar",
    "category": "UTILITY",
    "language_code": "ar",
    "language": "ar",
    "footer": "نفوذ التطوير",
    "template": (
        "مرحباً {{1}}\n"
        "تم تفعيل حسابك في منصة نفوذ التطوير.\n\n"
        "اسم المستخدم: {{2}}\n"
        "رابط الدخول: https://nufouth.com/login\n\n"
        "لتعيين كلمة المرور، استخدم خيار \"نسيت كلمة المرور\" من صفحة الدخول.\n"
        "نسعد دائماً بخدمتكم."
    ),
    "sample_values": "اسم المستأجر أو المالك,اسم المستخدم",
    "field_names": "contact_name,username",
    "status": "Draft",
}


def run():
    # Delete the rejected one (if present)
    if frappe.db.exists("WhatsApp Templates", REJECTED_NAME):
        frappe.delete_doc("WhatsApp Templates", REJECTED_NAME, ignore_permissions=True, force=True)
        print(f"✗ Deleted rejected template: {REJECTED_NAME}")

    # Insert the compliant replacement
    new_name = NEW_TEMPLATE["template_name"]
    if frappe.db.exists("WhatsApp Templates", {"template_name": new_name}):
        print(f"↷ Replacement already exists: {new_name}")
        return

    doc = frappe.get_doc({"doctype": "WhatsApp Templates", **NEW_TEMPLATE})
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"✓ Created compliant template: {doc.name}")
    print(
        "\nNext: open /app/whatsapp-templates/{name} and click Submit to re-send to Meta.\n"
        "For the password itself, send via email or let the user set it via \"forgot password\".".format(
            name=doc.name
        )
    )
    return doc.name
