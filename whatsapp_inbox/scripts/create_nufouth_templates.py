"""
Create Nufouth WhatsApp Templates.

Usage:
    bench --site <your-site> execute whatsapp_inbox.scripts.create_nufouth_templates.run

Creates 3 WhatsApp Templates:
    1. eid_greeting        — تهنئة عيد الأضحى
    2. user_credentials    — بيانات المستخدم في النظام
    3. marketing_offer     — فرصة تسويقية
"""

import frappe


TEMPLATES = [
    {
        "template_name": "eid_greeting_ar",
        "actual_name": "eid_greeting_ar",
        "arabic_label": "تهنئة عيد الأضحى",
        "category": "MARKETING",
        "language_code": "ar",
        "header": "",
        "footer": "نفوذ التطوير",
        "template": (
            "السيد/ {{1}}\n"
            "تهنئكم شركة نفوذ التطوير للعقارات وإدارة الأملاك بحلول عيد الأضحى المبارك\n"
            "سائلين المولى عز وجل أن يعيده عليكم باليمن والبركات"
        ),
        "sample_values": "اسم المستأجر أو المالك",
        "field_names": "contact_name",
    },
    {
        "template_name": "user_credentials_ar",
        "actual_name": "user_credentials_ar",
        "arabic_label": "بيانات المستخدم في النظام",
        "category": "UTILITY",
        "language_code": "ar",
        "header": "",
        "footer": "نفوذ التطوير",
        "template": (
            "السيد/ {{1}}\n"
            "نهديكم في نفوذ التطوير أطيب التحيات ونفيدكم بأنه تم إطلاق منصة نفوذ التطوير\n\n"
            "رابط المنصة: https://nufouth.com/login#login\n"
            "اسم المستخدم: {{2}}\n"
            "كلمة المرور: {{3}}\n"
            "رقم الواتساب المرتبط: {{4}}\n\n"
            "نتمنى لكم تجربة مميزة ونرحب باقتراحاتكم وملاحظاتكم للتطوير\n"
            "نسعد دائماً بخدمتكم"
        ),
        "sample_values": "اسم المستأجر أو المالك,اسم المستخدم,كلمة المرور,رقم الواتساب",
        "field_names": "contact_name,username,password,whatsapp_number",
    },
    {
        "template_name": "marketing_offer_ar",
        "actual_name": "marketing_offer_ar",
        "arabic_label": "فرصة تسويقية",
        "category": "MARKETING",
        "language_code": "ar",
        "header": "",
        "footer": "نفوذ التطوير",
        "template": (
            "فرصة مميزة ({{1}}) بحي ({{2}})\n"
            "({{3}})\n"
            "أسعار مميزة ومنافسة\n\n"
            "مع نفوذ التطوير .. عقارك بين ايديك\n"
            "لمتابعة آخر العروض بإمكانكم زيارة موقعنا الالكتروني\n"
            "https://nufouth.com\n"
            "الرقم الموحد 920010213\n"
            "الواتساب 966112161770"
        ),
        "sample_values": "للبيع أو للإيجار,اسم الحي,نوع العقار والتفاصيل",
        "field_names": "offer_type,neighborhood,property_details",
    },
]


def _ensure_language(code):
    """Make sure Language record exists so link field doesn't fail."""
    if not frappe.db.exists("Language", code):
        try:
            frappe.get_doc({
                "doctype": "Language",
                "language_code": code,
                "language_name": "Arabic" if code == "ar" else code,
            }).insert(ignore_permissions=True)
        except Exception:
            pass


def run():
    _ensure_language("ar")
    created = []
    skipped = []

    for tpl in TEMPLATES:
        name = tpl["template_name"]
        # Check by template_name OR actual_name to avoid duplicates
        existing = frappe.db.exists("WhatsApp Templates", {"template_name": name}) \
            or frappe.db.exists("WhatsApp Templates", {"actual_name": tpl["actual_name"]})
        if existing:
            skipped.append(name)
            continue

        fields = {
            "doctype": "WhatsApp Templates",
            "template_name": tpl["template_name"],
            "actual_name": tpl["actual_name"],
            "category": tpl["category"],
            "language": "ar",
            "language_code": tpl["language_code"],
            "footer": tpl.get("footer") or None,
            "template": tpl["template"],
            "sample_values": tpl.get("sample_values") or None,
            "field_names": tpl.get("field_names") or None,
            "status": "Draft",
        }
        # Only attach a header if text is provided (Meta rejects empty HEADER)
        if tpl.get("header"):
            fields["header"] = tpl["header"]
            fields["header_type"] = "TEXT"

        doc = frappe.get_doc(fields)
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
        created.append(doc.name)

    frappe.db.commit()

    print("\n" + "=" * 60)
    print(f"✓ Created: {len(created)} — {created}")
    print(f"↷ Skipped (already exist): {len(skipped)} — {skipped}")
    print("=" * 60)
    print(
        "\nNote: Templates are inserted with status=Draft in Frappe.\n"
        "Submit them to Meta for approval via /app/whatsapp-templates.\n"
    )
    return {"created": created, "skipped": skipped}
