import frappe
from frappe import publish_realtime


def _broadcast(event, message):
    """Broadcast a realtime event to all connected clients on this site.

    The same pattern used by whatsapp_chat app (no `user`, no `after_commit`).
    Empirically this reaches Administrator sessions; `user="all"` did not.
    """
    try:
        publish_realtime(event=event, message=message)
    except Exception as e:
        frappe.log_error(f"publish_realtime failed: {e}", "WhatsApp Inbox Realtime")


def _find_conversation(doc, create_if_missing=True):
    """Resolve conversation name from a WhatsApp Message doc.

    For incoming messages without a matching conversation, auto-create one so the
    inbox reflects new customer threads immediately.
    """
    if doc.get("conversation_id"):
        return doc.conversation_id
    phone = doc.get("from") if doc.type == "Incoming" else doc.get("to")
    if not phone:
        return None
    name = frappe.db.get_value("WhatsApp Conversation", {"phone_number": phone}, "name")
    if name or not create_if_missing or doc.type != "Incoming":
        return name
    try:
        conv = frappe.get_doc({
            "doctype": "WhatsApp Conversation",
            "phone_number": phone,
            "contact_name": doc.get("profile_name") or phone,
            "status": "Active",
            "last_message_at": frappe.utils.now(),
            "last_message_preview": (doc.get("message") or "")[:100],
            "last_message_type": "Incoming",
            "unread_count": 1,
            "total_messages": 1,
        }).insert(ignore_permissions=True)
        return conv.name
    except Exception as e:
        frappe.log_error(f"Auto-create conversation failed: {e}", "WhatsApp Inbox Realtime")
        return None


def _sender_name(doc):
    if doc.type == "Outgoing":
        owner = doc.get("owner")
        if owner and owner not in ("Administrator", "Guest"):
            full = frappe.db.get_value("User", owner, "full_name")
            if full:
                return full
        if owner == "Administrator":
            return frappe.db.get_value("User", owner, "full_name") or "Administrator"
        return "النظام"
    return doc.get("profile_name") or frappe.db.get_value(
        "WhatsApp Conversation", {"phone_number": doc.get("from")}, "contact_name"
    ) or doc.get("from")


def _message_payload(doc, conversation_name):
    return {
        "name": doc.name,
        "conversation": conversation_name,
        "type": doc.type,
        "from": doc.get("from"),
        "to": doc.get("to"),
        "message": doc.message,
        "content_type": doc.content_type,
        "attach": doc.get("attach"),
        "status": doc.get("status"),
        "creation": str(doc.creation) if doc.get("creation") else None,
        "is_reply": doc.get("is_reply"),
        "reply_to_message_id": doc.get("reply_to_message_id"),
        "message_id": doc.get("message_id"),
        "reference_doctype": doc.get("reference_doctype"),
        "reference_name": doc.get("reference_name"),
        "sender_name": _sender_name(doc),
    }


def on_message_insert(doc, method=None):
    conv = _find_conversation(doc)
    if not conv:
        return
    payload = _message_payload(doc, conv)
    _broadcast("whatsapp_inbox:new_message", payload)
    # Also bump the conversation's last message metadata so the sidebar updates
    try:
        frappe.db.set_value(
            "WhatsApp Conversation",
            conv,
            {
                "last_message_at": doc.creation or frappe.utils.now(),
                "last_message_preview": (doc.message or "")[:100],
                "last_message_type": doc.type,
                "unread_count": (
                    (frappe.db.get_value("WhatsApp Conversation", conv, "unread_count") or 0) + 1
                    if doc.type == "Incoming"
                    else 0
                ),
            },
        )
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Conversation update failed: {e}", "WhatsApp Inbox Realtime")


def on_message_update(doc, method=None):
    before = doc.get_doc_before_save()
    conv = _find_conversation(doc)
    if not conv:
        return

    # Attachment added after insert (webhook flow: message is inserted empty,
    # the file is saved and linked, then attach is set). Re-broadcast the full
    # payload so the UI can render the media.
    if before and not before.get("attach") and doc.get("attach"):
        _broadcast("whatsapp_inbox:new_message", _message_payload(doc, conv))
        return

    # Status change only
    if before and before.get("status") == doc.get("status"):
        return
    _broadcast("whatsapp_inbox:message_status", {
        "name": doc.name,
        "conversation": conv,
        "status": doc.get("status"),
        "error_message": doc.get("error_message"),
    })


def on_conversation_change(doc, method=None):
    _broadcast("whatsapp_inbox:conversation_update", {
        "name": doc.name,
        "phone_number": doc.get("phone_number"),
        "contact_name": doc.get("contact_name"),
        "status": doc.get("status"),
        "assigned_to": doc.get("assigned_to"),
        "last_message_at": str(doc.get("last_message_at")) if doc.get("last_message_at") else None,
        "last_message_preview": doc.get("last_message_preview"),
        "last_message_type": doc.get("last_message_type"),
        "unread_count": doc.get("unread_count"),
        "total_messages": doc.get("total_messages"),
    })
