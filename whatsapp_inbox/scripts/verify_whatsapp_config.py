"""
Verify that WhatsApp Settings talk to Meta correctly.

Run:
    echo "from whatsapp_inbox.scripts.verify_whatsapp_config import run; run()" \\
        | bench --site <site> console
"""

import frappe
import requests


def run():
    doc = frappe.get_doc("WhatsApp Settings")
    token = doc.get_password("token")

    print("=" * 60)
    print(f"App ID:       {doc.app_id}")
    print(f"Business ID:  {doc.business_id}")
    print(f"Phone ID:     {doc.phone_id}")
    print(f"Version:      {doc.version}")
    print(f"Token len:    {len(token) if token else 0} chars")
    print(f"Enabled:      {doc.enabled}")
    print("=" * 60)

    if not token:
        print("✗ No token set")
        return

    base = f"{doc.url}/{doc.version}"

    # 1) Token validity
    r = requests.get(f"{base}/me", params={"access_token": token})
    if r.status_code == 200:
        print(f"✓ Token valid: {r.json()}")
    else:
        print(f"✗ Token invalid: {r.status_code} {r.text[:200]}")
        return

    # 2) Phone exists + status
    r = requests.get(
        f"{base}/{doc.phone_id}",
        params={
            "access_token": token,
            "fields": "display_phone_number,verified_name,code_verification_status,quality_rating,webhook_configuration",
        },
    )
    if r.status_code == 200:
        data = r.json()
        print(f"✓ Phone: {data.get('display_phone_number')} — {data.get('verified_name')}")
        print(f"  Verification: {data.get('code_verification_status')}")
        print(f"  Quality: {data.get('quality_rating')}")
        wh = (data.get("webhook_configuration") or {}).get("application")
        if wh:
            print(f"  Webhook URL registered: {wh}")
    else:
        print(f"✗ Phone ID problem: {r.status_code} {r.text[:200]}")

    # 3) List phones in business
    r = requests.get(f"{base}/{doc.business_id}/phone_numbers", params={"access_token": token})
    if r.status_code == 200:
        print("\nAll phones in business account:")
        for p in r.json().get("data", []):
            print(f"  • {p.get('display_phone_number')} (id={p.get('id')}) — {p.get('code_verification_status')}")
    else:
        print(f"✗ Cannot list business phones: {r.status_code}")
