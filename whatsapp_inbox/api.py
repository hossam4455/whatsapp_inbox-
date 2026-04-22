import json

import frappe
from frappe import _

_SETTINGS_KEY = "whatsapp_inbox_settings"

_DEFAULT_SETTINGS = {
    "work_days": [0, 1, 2, 3, 4],  # Sun..Thu (0=Sun per form layout)
    "start_time": "09:00",
    "end_time": "18:00",
    "timezone": "Asia/Riyadh",
    "holidays": [],  # [{date, name}]
}


@frappe.whitelist()
def get_inbox_settings():
    raw = frappe.db.get_default(_SETTINGS_KEY)
    if not raw:
        return dict(_DEFAULT_SETTINGS)
    try:
        data = json.loads(raw)
    except Exception:
        return dict(_DEFAULT_SETTINGS)
    # Fill missing keys with defaults
    for k, v in _DEFAULT_SETTINGS.items():
        data.setdefault(k, v)
    return data


@frappe.whitelist()
def save_inbox_settings(settings):
    if isinstance(settings, str):
        settings = json.loads(settings)
    # Keep only known fields
    clean = {}
    for k, v in _DEFAULT_SETTINGS.items():
        if k in settings:
            clean[k] = settings[k]
        else:
            clean[k] = v
    frappe.db.set_default(_SETTINGS_KEY, json.dumps(clean))
    frappe.db.commit()
    return {"success": True, "settings": clean}


@frappe.whitelist()
def get_conversations(filters=None, search=None, page=1, page_length=30):
    """Get conversations list with pagination."""
    conditions = ["1=1"]
    values = {}
    page = int(page)
    page_length = int(page_length)

    if filters == "unread":
        conditions.append("c.unread_count > 0")
    elif filters == "mine":
        conditions.append("c.assigned_to = %(user)s")
        values["user"] = frappe.session.user
    elif filters == "escalated":
        conditions.append("c.status = 'Escalated'")
    elif filters == "closed":
        conditions.append("c.status = 'Closed'")
    else:
        conditions.append("c.status != 'Closed'")

    if search:
        conditions.append("(c.phone_number LIKE %(search)s OR c.contact_name LIKE %(search)s)")
        values["search"] = f"%{search}%"

    where = " AND ".join(conditions)
    offset = (page - 1) * page_length

    conversations = frappe.db.sql(f"""
        SELECT c.name, c.phone_number, c.contact_name, c.contact,
               c.assigned_to, c.status, c.priority,
               c.last_message_at, c.last_message_preview, c.last_message_type,
               c.unread_count, c.total_messages,
               c.linked_tenant, c.linked_owner, c.linked_property
        FROM `tabWhatsApp Conversation` c
        WHERE {where}
        ORDER BY c.last_message_at DESC
        LIMIT {page_length} OFFSET {offset}
    """, values, as_dict=True)

    # Get assigned user full names
    for conv in conversations:
        if conv.get("assigned_to"):
            conv["assigned_name"] = frappe.db.get_value("User", conv["assigned_to"], "full_name")

    total = frappe.db.sql(f"""
        SELECT COUNT(*) FROM `tabWhatsApp Conversation` c WHERE {where}
    """, values)[0][0]

    return {
        "conversations": conversations,
        "total": total,
        "page": page,
        "page_length": page_length,
        "has_more": (page * page_length) < total,
    }


@frappe.whitelist()
def get_messages(conversation, page=1, page_length=50):
    """Get messages for a conversation with pagination (newest first)."""
    page = int(page)
    page_length = int(page_length)
    offset = (page - 1) * page_length

    conv = frappe.get_doc("WhatsApp Conversation", conversation)

    messages = frappe.db.sql("""
        SELECT m.name, m.`from`, m.`to`, m.type, m.message_type, m.content_type,
               m.message, m.attach, m.creation, m.status,
               m.is_reply, m.reply_to_message_id,
               m.reference_doctype, m.reference_name,
               m.profile_name, m.owner,
               u.full_name AS sender_full_name
        FROM `tabWhatsApp Message` m
        LEFT JOIN `tabUser` u ON u.name = m.owner
        WHERE (m.`from` = %(phone)s OR m.`to` = %(phone)s)
        ORDER BY m.creation DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """, {
        "phone": conv.phone_number,
        "limit": page_length,
        "offset": offset,
    }, as_dict=True)

    # Resolve display name per message
    customer_name = conv.contact_name or conv.phone_number
    for m in messages:
        if m.type == "Outgoing":
            if m.owner and m.owner not in ("Administrator", "Guest") and m.sender_full_name:
                m["sender_name"] = m.sender_full_name
            elif m.owner == "Administrator":
                m["sender_name"] = m.sender_full_name or "Administrator"
            else:
                m["sender_name"] = "النظام"
        else:
            m["sender_name"] = m.profile_name or customer_name

    # Reverse to show oldest first in chat
    messages.reverse()

    total = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabWhatsApp Message`
        WHERE `from` = %(phone)s OR `to` = %(phone)s
    """, {"phone": conv.phone_number})[0][0]

    return {
        "messages": messages,
        "total": total,
        "has_more": (page * page_length) < total,
        "conversation": {
            "name": conv.name,
            "phone_number": conv.phone_number,
            "contact_name": conv.contact_name,
            "status": conv.status,
            "assigned_to": conv.assigned_to,
        },
    }


def _is_admin(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    return ("Administrator" == user) or ("System Manager" in roles)


def _check_lock(conv):
    """Raise if the current user is not the one who locked the conversation.

    Admins/System Managers can always reply. If `assigned_to` is empty the
    conversation is free — anyone may reply."""
    if _is_admin():
        return
    holder = conv.assigned_to
    if not holder:
        return
    if holder != frappe.session.user:
        full = frappe.db.get_value("User", holder, "full_name") or holder
        frappe.throw(_("🔒 هذه المحادثة محجوزة حالياً مع {0}").format(full),
                     title=_("غير مسموح بالرد"))


@frappe.whitelist()
def acquire_conversation_lock(conversation):
    """Lock a conversation to the current user. If another user already
    holds the lock, return who — UI will show a banner instead of locking."""
    conv = frappe.get_doc("WhatsApp Conversation", conversation)
    current = frappe.session.user

    # Already mine → nothing to do
    if conv.assigned_to == current:
        return {"locked": True, "holder": current, "mine": True}

    # Someone else holds it → leave it
    if conv.assigned_to and conv.assigned_to != current:
        full = frappe.db.get_value("User", conv.assigned_to, "full_name") or conv.assigned_to
        return {
            "locked": True,
            "mine": False,
            "holder": conv.assigned_to,
            "holder_name": full,
        }

    # Free → acquire
    frappe.db.set_value("WhatsApp Conversation", conv.name, "assigned_to", current)
    frappe.db.commit()
    return {"locked": True, "holder": current, "mine": True}


@frappe.whitelist()
def release_conversation_lock(conversation):
    """Clear the lock only if the caller holds it. Admins can force-release."""
    conv = frappe.get_doc("WhatsApp Conversation", conversation)
    if conv.assigned_to and conv.assigned_to != frappe.session.user and not _is_admin():
        return {"released": False, "reason": "not_holder"}
    frappe.db.set_value("WhatsApp Conversation", conv.name, "assigned_to", None)
    frappe.db.commit()
    return {"released": True}


@frappe.whitelist()
def send_reply(conversation, message):
    """Send a text reply to a conversation."""
    conv = frappe.get_doc("WhatsApp Conversation", conversation)
    _check_lock(conv)

    # Create outgoing WhatsApp Message
    msg = frappe.get_doc({
        "doctype": "WhatsApp Message",
        "type": "Outgoing",
        "message_type": "Manual",
        "to": conv.phone_number,
        "message": message,
        "content_type": "text",
        "conversation_id": conv.name,
    })
    msg.insert(ignore_permissions=True)

    # Update conversation
    conv.last_message_at = frappe.utils.now()
    conv.last_message_preview = message[:100] if message else ""
    conv.last_message_type = "Outgoing"
    conv.status = "Replied"
    conv.unread_count = 0
    conv.total_messages = (conv.total_messages or 0) + 1
    conv.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "success": True,
        "message_id": msg.name,
        "status": msg.status,
    }


def _resolve_ffmpeg():
    """Locate an ffmpeg binary. Prefers imageio-ffmpeg (pip-installed, ships
    with a bundled binary), falls back to a system ffmpeg on PATH."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        import shutil
        return shutil.which("ffmpeg")


def _transcode_audio_to_ogg_opus(src_path):
    """Transcode audio to OGG/OPUS (Meta WhatsApp API compatible). Returns new path or None on failure."""
    import os
    import subprocess

    ffmpeg = _resolve_ffmpeg()
    if not ffmpeg:
        frappe.log_error(
            "ffmpeg binary not available (install imageio-ffmpeg or system ffmpeg).",
            "WhatsApp Voice Transcode",
        )
        return None

    dst_path = os.path.splitext(src_path)[0] + "_ogg.ogg"
    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", src_path, "-vn", "-c:a", "libopus", "-b:a", "32k", "-ar", "48000", "-ac", "1", dst_path],
            check=True,
            capture_output=True,
            timeout=60,
        )
        return dst_path
    except Exception as e:
        frappe.log_error(f"ffmpeg transcode failed: {e}", "WhatsApp Voice Transcode")
        return None


@frappe.whitelist()
def send_media(conversation, file_url, filename, content_type="document", caption=""):
    """Send a file/image to a conversation."""
    import os
    import shutil
    import hashlib

    conv = frappe.get_doc("WhatsApp Conversation", conversation)
    _check_lock(conv)

    # Rename file to English name for Meta API compatibility
    if file_url and not file_url.startswith("http"):
        original_path = frappe.get_site_path("public", file_url.lstrip("/"))
        if os.path.exists(original_path):
            # For audio, transcode to OGG/OPUS (Meta requirement — browser MediaRecorder
            # usually outputs WebM/Opus labeled as .ogg, which Meta silently rejects).
            if content_type == "audio":
                transcoded = _transcode_audio_to_ogg_opus(original_path)
                if transcoded and os.path.exists(transcoded):
                    original_path = transcoded
                    file_url = os.path.splitext(file_url)[0] + "_ogg.ogg"
            ext = os.path.splitext(file_url)[1] or (".ogg" if content_type == "audio" else ".pdf")
            short_hash = hashlib.md5(file_url.encode()).hexdigest()[:10]
            new_name = f"wa_send_{short_hash}{ext}"
            new_url = f"/files/{new_name}"
            new_path = frappe.get_site_path("public", "files", new_name)
            if not os.path.exists(new_path):
                shutil.copy2(original_path, new_path)
            file_url = new_url

    msg = frappe.get_doc({
        "doctype": "WhatsApp Message",
        "type": "Outgoing",
        "message_type": "Manual",
        "to": conv.phone_number,
        "message": caption or filename,
        "attach": file_url,
        "content_type": content_type,
        "conversation_id": conv.name,
    })
    msg.insert(ignore_permissions=True)

    conv.last_message_at = frappe.utils.now()
    conv.last_message_preview = (caption or filename)[:100]
    conv.last_message_type = "Outgoing"
    conv.status = "Replied"
    conv.total_messages = (conv.total_messages or 0) + 1
    conv.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message_id": msg.name,
        "status": msg.status,
    }


@frappe.whitelist()
def get_conversation_stats(conversation):
    """Return computed dashboard stats for a conversation."""
    conv = frappe.get_doc("WhatsApp Conversation", conversation)

    counts = frappe.db.sql("""
        SELECT type, COUNT(*) AS n
        FROM `tabWhatsApp Message`
        WHERE `from` = %(phone)s OR `to` = %(phone)s
        GROUP BY type
    """, {"phone": conv.phone_number}, as_dict=True)
    incoming = outgoing = 0
    for row in counts:
        if row.type == "Incoming":
            incoming = row.n
        elif row.type == "Outgoing":
            outgoing = row.n

    last_incoming = frappe.db.get_value(
        "WhatsApp Message",
        {"from": conv.phone_number, "type": "Incoming"},
        "creation",
        order_by="creation desc",
    )

    last_msg = frappe.db.sql("""
        SELECT name, type, creation, message, content_type
        FROM `tabWhatsApp Message`
        WHERE `from` = %(phone)s OR `to` = %(phone)s
        ORDER BY creation DESC LIMIT 1
    """, {"phone": conv.phone_number}, as_dict=True)
    last = last_msg[0] if last_msg else None

    assigned_name = None
    if conv.assigned_to:
        assigned_name = frappe.db.get_value("User", conv.assigned_to, "full_name")

    return {
        "name": conv.name,
        "phone_number": conv.phone_number,
        "contact_name": conv.contact_name,
        "status": conv.status,
        "priority": conv.priority,
        "assigned_to": conv.assigned_to,
        "assigned_name": assigned_name,
        "unread_count": conv.unread_count,
        "total_messages": conv.total_messages,
        "incoming_count": incoming,
        "outgoing_count": outgoing,
        "last_incoming_at": str(last_incoming) if last_incoming else None,
        "last_message_at": str(last.creation) if last else None,
        "last_message_type": last.type if last else None,
        "last_message_preview": (last.message or "")[:200] if last else None,
        "first_response_time": conv.first_response_time,
        "linked_tenant": conv.linked_tenant,
        "linked_owner": conv.linked_owner,
        "linked_property": conv.linked_property,
        "internal_notes": conv.internal_notes,
    }


@frappe.whitelist()
def update_conversation(conversation, **kwargs):
    """Update conversation fields (assigned_to, priority, status, internal_notes, etc)."""
    allowed = {"assigned_to", "priority", "status", "internal_notes",
               "linked_tenant", "linked_owner", "linked_property", "contact_name"}
    conv = frappe.get_doc("WhatsApp Conversation", conversation)
    changed = False
    for k, v in kwargs.items():
        if k in allowed:
            conv.set(k, v or None)
            changed = True
    if changed:
        conv.save(ignore_permissions=True)
        frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def mark_as_read(conversation):
    """Mark conversation as read."""
    frappe.db.set_value("WhatsApp Conversation", conversation, "unread_count", 0)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def retry_message(message_id):
    """Retry sending a failed outgoing WhatsApp Message."""
    msg = frappe.get_doc("WhatsApp Message", message_id)
    if msg.type != "Outgoing":
        frappe.throw(_("Only outgoing messages can be retried"))
    msg.status = ""
    msg.error_message = None
    msg.send_message()
    msg.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": msg.status == "Success", "status": msg.status, "error": msg.error_message}


@frappe.whitelist()
def transcribe_voice(message_id):
    """Transcribe a voice message using OpenAI Whisper.

    Requires `openai_api_key` in site_config.json (or the OPENAI_API_KEY env var).
    """
    import os

    msg = frappe.get_doc("WhatsApp Message", message_id)
    if msg.content_type != "audio" or not msg.attach:
        return {"error": "ليست رسالة صوتية"}

    api_key = frappe.conf.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "لم يتم ضبط OpenAI API key في site_config.json"}

    attach = msg.attach
    if attach.startswith("/"):
        path = frappe.get_site_path("public", attach.lstrip("/")) if attach.startswith("/files/") \
            else frappe.get_site_path(attach.lstrip("/"))
    elif attach.startswith("http"):
        # download to temp
        import tempfile
        import requests
        r = requests.get(attach, timeout=30)
        if r.status_code != 200:
            return {"error": "تعذر تحميل الملف"}
        tf = tempfile.NamedTemporaryFile(suffix=os.path.splitext(attach)[1] or ".ogg", delete=False)
        tf.write(r.content)
        tf.close()
        path = tf.name
    else:
        path = frappe.get_site_path("public", "files", attach)

    if not os.path.exists(path):
        return {"error": "الملف غير موجود"}

    try:
        import requests
        with open(path, "rb") as f:
            r = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (os.path.basename(path), f, "audio/ogg")},
                data={"model": "whisper-1"},
                timeout=120,
            )
        if r.status_code != 200:
            return {"error": f"Whisper API: {r.status_code}"}
        text = (r.json() or {}).get("text", "").strip()
        return {"text": text}
    except Exception as e:
        frappe.log_error(f"Whisper transcription failed: {e}", "WhatsApp Transcription")
        return {"error": str(e)}


@frappe.whitelist()
def get_campaigns(status=None):
    """Return WhatsApp bulk campaigns with computed stats."""
    conditions = []
    values = {}
    if status and status != "all":
        conditions.append("b.status = %(status)s")
        values["status"] = status
    where = " AND ".join(conditions) if conditions else "1=1"

    campaigns = frappe.db.sql(f"""
        SELECT b.name, b.title, b.template, b.from_number,
               b.recipient_count, b.sent_count, b.status,
               b.scheduled_time, b.creation, b.modified,
               b.owner
        FROM `tabBulk WhatsApp Message` b
        WHERE {where}
        ORDER BY b.creation DESC
        LIMIT 100
    """, values, as_dict=True)

    # Compute per-campaign stats from WhatsApp Message
    total_delivered = total_read = total_failed = total_targets = 0
    for c in campaigns:
        stats = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN status IN ('sent', 'delivered', 'read', 'Success') THEN 1 ELSE 0 END) AS delivered,
                SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) AS read_count,
                SUM(CASE WHEN status IN ('failed', 'error') THEN 1 ELSE 0 END) AS failed,
                COUNT(*) AS total
            FROM `tabWhatsApp Message`
            WHERE bulk_message_reference = %(b)s
        """, {"b": c.name}, as_dict=True)[0]
        c["delivered"] = int(stats.delivered or 0)
        c["read"] = int(stats.read_count or 0)
        c["failed"] = int(stats.failed or 0)
        c["processed"] = int(stats.total or 0)
        c["targets"] = int(c.recipient_count or stats.total or 0)
        total_delivered += c["delivered"]
        total_read += c["read"]
        total_failed += c["failed"]
        total_targets += c["targets"]

    # Status counts
    status_rows = frappe.db.sql("""
        SELECT status, COUNT(*) AS n FROM `tabBulk WhatsApp Message` GROUP BY status
    """, as_dict=True)
    status_counts = {r.status: r.n for r in status_rows}
    total = sum(status_counts.values())

    def pct(num, den):
        return round((num / den) * 100, 1) if den else 0

    return {
        "campaigns": campaigns,
        "status_counts": {
            "all": total,
            "ongoing": status_counts.get("In Progress", 0) + status_counts.get("Queued", 0),
            "completed": status_counts.get("Completed", 0),
            "scheduled": status_counts.get("Queued", 0),
            "draft": status_counts.get("Draft", 0),
            "cancelled": status_counts.get("Cancelled", 0) + status_counts.get("Partially Failed", 0),
        },
        "summary": {
            "delivered_pct": pct(total_delivered, total_targets),
            "read_pct": pct(total_read, total_targets),
            "failed_pct": pct(total_failed, total_targets),
            "delivered": total_delivered,
            "read": total_read,
            "failed": total_failed,
            "targets": total_targets,
            "campaigns_count": total,
            "completed_count": status_counts.get("Completed", 0),
        },
    }


@frappe.whitelist()
def get_campaign_detail(campaign):
    """Return a single campaign with recipient-level events."""
    c = frappe.get_doc("Bulk WhatsApp Message", campaign)

    messages = frappe.db.sql("""
        SELECT name, `to`, status, creation, message, error_message, message_id
        FROM `tabWhatsApp Message`
        WHERE bulk_message_reference = %(b)s
        ORDER BY creation DESC
    """, {"b": campaign}, as_dict=True)

    delivered = sum(1 for m in messages if (m.status or '').lower() in ('sent', 'delivered', 'read', 'success'))
    read = sum(1 for m in messages if (m.status or '').lower() == 'read')
    failed = sum(1 for m in messages if (m.status or '').lower() in ('failed', 'error'))
    processed = len(messages)

    # Recipient list
    recipients = []
    for r in (c.recipients or []):
        recipients.append({
            "mobile_number": r.mobile_number,
            "recipient_name": r.recipient_name,
        })

    return {
        "name": c.name,
        "title": c.title,
        "template": c.template,
        "from_number": c.from_number,
        "status": c.status,
        "scheduled_time": str(c.scheduled_time) if c.scheduled_time else None,
        "creation": str(c.creation),
        "modified": str(c.modified),
        "recipient_count": c.recipient_count or len(recipients),
        "sent_count": c.sent_count,
        "recipient_type": c.recipient_type,
        "recipient_list": c.recipient_list,
        "stats": {
            "targets": c.recipient_count or len(recipients) or processed,
            "processed": processed,
            "delivered": delivered,
            "read": read,
            "failed": failed,
        },
        "recipients": recipients,
        "messages": messages,
    }


@frappe.whitelist()
def get_templates(status=None, search=None):
    """List WhatsApp templates with summary."""
    conditions = []
    values = {}
    if status and status != "all":
        conditions.append("LOWER(IFNULL(status, '')) LIKE %(st)s")
        values["st"] = status.lower()
    if search:
        conditions.append("(template_name LIKE %(s)s OR actual_name LIKE %(s)s)")
        values["s"] = f"%{search}%"
    where = " AND ".join(conditions) if conditions else "1=1"

    templates = frappe.db.sql(f"""
        SELECT name, template_name, actual_name, language_code, category,
               status, header, footer, template, creation, modified
        FROM `tabWhatsApp Templates`
        WHERE {where}
        ORDER BY modified DESC
        LIMIT 200
    """, values, as_dict=True)

    status_counts = frappe.db.sql("""
        SELECT LOWER(IFNULL(status, '')) AS s, COUNT(*) AS n
        FROM `tabWhatsApp Templates` GROUP BY LOWER(IFNULL(status, ''))
    """, as_dict=True)
    counts = {r.s: r.n for r in status_counts}

    return {
        "templates": templates,
        "status_counts": {
            "all": sum(counts.values()),
            "approved": counts.get("approved", 0),
            "pending": counts.get("pending", 0) + counts.get("in review", 0),
            "rejected": counts.get("rejected", 0),
        },
    }


@frappe.whitelist()
def get_analytics(period_days=30):
    """Return WhatsApp analytics: response time, agent leaderboard, SLA, etc."""
    period_days = int(period_days or 30)
    from_date = frappe.utils.add_days(frappe.utils.now_datetime(), -period_days)

    # Average response time: for each incoming message, time until next outgoing
    # to same contact. Compute average in minutes, over the period.
    avg_row = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(MINUTE, i.creation, (
            SELECT MIN(o.creation) FROM `tabWhatsApp Message` o
            WHERE o.type = 'Outgoing' AND o.`to` = i.`from` AND o.creation > i.creation
        ))) AS avg_minutes
        FROM `tabWhatsApp Message` i
        WHERE i.type = 'Incoming' AND i.creation >= %(d)s
    """, {"d": from_date}, as_dict=True)
    avg_minutes = int(avg_row[0].avg_minutes or 0) if avg_row else 0
    avg_hours = avg_minutes // 60
    avg_rem_minutes = avg_minutes % 60

    # Awaiting response: conversations whose last message is Incoming
    waiting_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabWhatsApp Conversation`
        WHERE last_message_type = 'Incoming' AND IFNULL(status, '') != 'Closed'
    """)[0][0] or 0

    # Top agents by outgoing message count
    top_agents = frappe.db.sql("""
        SELECT m.owner, COALESCE(u.full_name, m.owner) AS name,
               COUNT(*) AS messages,
               COUNT(DISTINCT m.`to`) AS conversations
        FROM `tabWhatsApp Message` m
        LEFT JOIN `tabUser` u ON u.name = m.owner
        WHERE m.type = 'Outgoing' AND m.creation >= %(d)s
          AND m.owner IS NOT NULL AND m.owner NOT IN ('Administrator', 'Guest')
        GROUP BY m.owner
        ORDER BY messages DESC
        LIMIT 5
    """, {"d": from_date}, as_dict=True)

    # SLA breakdown: for conversations awaiting reply
    sla = frappe.db.sql("""
        SELECT
            SUM(CASE WHEN TIMESTAMPDIFF(MINUTE, last_message_at, NOW()) >= 60 THEN 1 ELSE 0 END) AS critical,
            SUM(CASE WHEN TIMESTAMPDIFF(MINUTE, last_message_at, NOW()) >= 10
                     AND TIMESTAMPDIFF(MINUTE, last_message_at, NOW()) < 60 THEN 1 ELSE 0 END) AS warning
        FROM `tabWhatsApp Conversation`
        WHERE last_message_type = 'Incoming' AND IFNULL(status, '') != 'Closed'
    """, as_dict=True)[0]

    # Team distribution (awaiting conversations per assigned user)
    team = frappe.db.sql("""
        SELECT COALESCE(u.full_name, c.assigned_to, 'Unassigned') AS name,
               COUNT(*) AS awaiting
        FROM `tabWhatsApp Conversation` c
        LEFT JOIN `tabUser` u ON u.name = c.assigned_to
        WHERE c.last_message_type = 'Incoming' AND IFNULL(c.status, '') != 'Closed'
        GROUP BY COALESCE(c.assigned_to, 'Unassigned')
        ORDER BY awaiting DESC
        LIMIT 10
    """, as_dict=True)

    # Most mentioned property type (from linked_property → property type, if available) or tags
    top_type = frappe.db.sql("""
        SELECT tags_list AS label, COUNT(*) AS n
        FROM `tabWhatsApp Conversation`
        WHERE IFNULL(tags_list, '') != ''
        GROUP BY tags_list ORDER BY n DESC LIMIT 1
    """, as_dict=True)
    top_type_label = top_type[0].label if top_type else None

    # Response speed status
    if avg_minutes == 0:
        response_status = "لا توجد بيانات"
        response_status_class = "neutral"
    elif avg_minutes < 30:
        response_status = "ممتاز"
        response_status_class = "good"
    elif avg_minutes < 120:
        response_status = "جيد"
        response_status_class = "ok"
    elif avg_minutes < 360:
        response_status = "يحتاج تحسين"
        response_status_class = "warn"
    else:
        response_status = "ضعيف"
        response_status_class = "danger"

    # Total messages + conversations
    totals = frappe.db.sql("""
        SELECT
            (SELECT COUNT(*) FROM `tabWhatsApp Message` WHERE creation >= %(d)s) AS messages,
            (SELECT COUNT(*) FROM `tabWhatsApp Conversation`) AS conversations,
            (SELECT COUNT(*) FROM `tabWhatsApp Conversation` WHERE IFNULL(status,'') != 'Closed') AS open_conv
    """, {"d": from_date}, as_dict=True)[0]

    return {
        "period_days": period_days,
        "avg_response": {
            "minutes": avg_minutes,
            "hours": avg_hours,
            "rem_minutes": avg_rem_minutes,
            "status": response_status,
            "status_class": response_status_class,
        },
        "waiting_count": int(waiting_count),
        "top_agents": top_agents,
        "sla": {
            "critical": int(sla.critical or 0),
            "warning": int(sla.warning or 0),
        },
        "team_distribution": team,
        "top_property_type": top_type_label,
        "totals": {
            "messages": int(totals.messages or 0),
            "conversations": int(totals.conversations or 0),
            "open_conversations": int(totals.open_conv or 0),
        },
    }
