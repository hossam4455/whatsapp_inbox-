import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";

// Expose mount function for Frappe Page
window.mountWhatsAppInbox = function (el) {
  if (el._vue_mounted) return;
  const app = createApp(App);
  app.use(createPinia());
  app.mount(el);
  el._vue_mounted = true;
};
