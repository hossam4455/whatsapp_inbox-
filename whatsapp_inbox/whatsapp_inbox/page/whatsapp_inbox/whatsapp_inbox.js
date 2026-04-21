frappe.pages["whatsapp-inbox"].on_page_load = function (wrapper) {
  frappe.ui.make_app_page({
    parent: wrapper,
    title: "WhatsApp Inbox",
    single_column: true,
  });

  $(wrapper).find(".layout-main-section").html(
    '<div id="whatsapp-inbox-app"><div style="text-align:center;padding:60px;color:#6c757d;">جاري التحميل...</div></div>'
  );

  // Cache-bust with build timestamp
  var cssHref = "/assets/whatsapp_inbox/dist/whatsapp_inbox.css?v=" + Date.now();
  var jsSrc = "/assets/whatsapp_inbox/dist/whatsapp_inbox.iife.js?v=" + Date.now();

  // Load CSS
  if (!document.getElementById("wa-inbox-css")) {
    var link = document.createElement("link");
    link.id = "wa-inbox-css";
    link.rel = "stylesheet";
    link.href = cssHref;
    document.head.appendChild(link);
  }

  // Load JS then mount
  if (window.mountWhatsAppInbox) {
    mountApp();
  } else {
    var script = document.createElement("script");
    script.src = jsSrc;
    script.onload = function () { mountApp(); };
    script.onerror = function () {
      document.getElementById("whatsapp-inbox-app").innerHTML =
        '<div style="text-align:center;padding:60px;color:#e74c3c;"><h3>Failed to load</h3></div>';
    };
    document.head.appendChild(script);
  }

  function mountApp() {
    var el = document.getElementById("whatsapp-inbox-app");
    if (el && window.mountWhatsAppInbox) {
      window.mountWhatsAppInbox(el);
    }
  }
};
