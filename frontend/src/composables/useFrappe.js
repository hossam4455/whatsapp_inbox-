export function useFrappe() {
  const call = (method, args = {}) => {
    return new Promise((resolve, reject) => {
      frappe.call({
        method: `whatsapp_inbox.api.${method}`,
        args,
        callback: (r) => resolve(r.message),
        error: (e) => reject(e),
      });
    });
  };

  const onRealtime = (event, callback) => {
    frappe.realtime.on(event, callback);
  };

  const offRealtime = (event, callback) => {
    frappe.realtime.off(event, callback);
  };

  return { call, onRealtime, offRealtime };
}
