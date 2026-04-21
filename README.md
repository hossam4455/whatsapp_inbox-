# WhatsApp Inbox

A modern WhatsApp conversation management app for Frappe / ERPNext, built with Vue 3.

## Requirements

- Frappe v15+
- The [`frappe_whatsapp`](https://github.com/shridarpatil/frappe_whatsapp) app installed on the same site
- `ffmpeg` (optional but recommended) — for transcoding voice notes to the OGG/OPUS container that Meta's API accepts

Install ffmpeg once on the server:

```bash
sudo apt install ffmpeg -y
```

## Install on Frappe Cloud

1. Go to your site → **Apps** → **Add App** → **Public Apps**
2. Search for `whatsapp_inbox` (or paste this repo URL in **Install from GitHub**)
3. Select the `main` branch, deploy
4. Make sure `frappe_whatsapp` is also installed on the site

## Install on a local bench

```bash
cd ~/frappe-bench
bench get-app https://github.com/hossam4455/whatsapp_inbox-
bench --site YOUR-SITE install-app whatsapp_inbox
bench --site YOUR-SITE migrate
bench restart
```

## Setup

1. Open `/app/whatsapp-settings` and fill in your Meta WhatsApp Cloud API credentials:
   - App ID
   - Permanent Access Token
   - Business Account ID
   - Phone Number ID
   - Webhook Verify Token (any random string)
2. In Meta Developers → App → WhatsApp → **Configuration** → Webhook:
   - Callback URL: `https://YOUR-SITE/api/method/frappe_whatsapp.utils.webhook.webhook`
   - Verify Token: the same string you set in Frappe
   - Subscribe to: `messages`, `message_status`, `message_template_status_update`
3. Toggle **Enabled** in WhatsApp Settings → Save
4. Open the inbox at: `/app/whatsapp-inbox`

## License

MIT
