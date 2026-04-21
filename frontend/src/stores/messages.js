import { defineStore } from "pinia";
import { ref } from "vue";
import { useFrappe } from "@/composables/useFrappe";

export const useMessagesStore = defineStore("messages", () => {
  const { call, onRealtime, offRealtime } = useFrappe();

  const messages = ref([]);
  const loading = ref(false);
  const sending = ref(false);
  const page = ref(1);
  const hasMore = ref(false);
  const conversationInfo = ref(null);
  const activeConversation = ref(null);

  let newMessageHandler = null;
  let statusHandler = null;

  async function fetchMessages(conversation, reset = true) {
    if (reset) {
      page.value = 1;
      messages.value = [];
    }
    loading.value = true;
    try {
      const data = await call("get_messages", {
        conversation,
        page: page.value,
      });
      if (reset) {
        messages.value = data.messages;
      } else {
        messages.value = [...data.messages, ...messages.value];
      }
      hasMore.value = data.has_more;
      conversationInfo.value = data.conversation;

      // Mark as read
      call("mark_as_read", { conversation });
    } finally {
      loading.value = false;
    }
  }

  async function sendReply(conversation, message) {
    sending.value = true;
    try {
      const result = await call("send_reply", { conversation, message });
      // Add to local messages
      messages.value.push({
        name: result.message_id,
        type: "Outgoing",
        message: message,
        creation: new Date().toISOString(),
        status: result.status,
        content_type: "text",
      });
      return result;
    } finally {
      sending.value = false;
    }
  }

  async function sendFile(conversation, file, caption) {
    sending.value = true;
    try {
      // Upload file via fetch
      const formData = new FormData();
      formData.append("file", file, file.name);
      formData.append("is_private", "0");

      const uploadResponse = await fetch("/api/method/upload_file", {
        method: "POST",
        headers: {
          "X-Frappe-CSRF-Token": frappe.csrf_token,
        },
        body: formData,
      });
      const uploadData = await uploadResponse.json();
      console.log("Upload response:", uploadData);
      const fileUrl = uploadData.message?.file_url
        || uploadData.file_url
        || (uploadData.message && uploadData.message.file_url)
        || "/files/" + file.name;

      // Send via API
      const result = await call("send_media", {
        conversation,
        file_url: fileUrl,
        filename: file.name,
        content_type: file.type.startsWith("image/") ? "image" : file.type.startsWith("audio/") ? "audio" : "document",
        caption: caption || "",
      });

      const ctype = file.type.startsWith("image/") ? "image" : file.type.startsWith("audio/") ? "audio" : "document";
      messages.value.push({
        name: result.message_id,
        type: "Outgoing",
        message: caption || (ctype === "audio" ? "🎤 رسالة صوتية" : file.name),
        attach: fileUrl,
        creation: new Date().toISOString(),
        status: result.status,
        content_type: ctype,
      });
      return result;
    } finally {
      sending.value = false;
    }
  }

  async function loadOlder(conversation) {
    if (hasMore.value && !loading.value) {
      page.value++;
      await fetchMessages(conversation, false);
    }
  }

  function subscribe(conversationName) {
    unsubscribe();
    activeConversation.value = conversationName;

    newMessageHandler = (payload) => {
      console.log("[wa-inbox] new_message received:", payload, "activeConv:", activeConversation.value);
      if (!payload) return;
      const matchesActive =
        !payload.conversation ||
        payload.conversation === activeConversation.value;
      if (!matchesActive) return;

      const idx = messages.value.findIndex((m) => m.name === payload.name);
      if (idx !== -1) {
        // Second broadcast (attach added after insert) — merge into existing row
        messages.value = messages.value.map((m, i) =>
          i === idx ? { ...m, ...payload } : m
        );
      } else {
        // New message
        messages.value = [...messages.value, payload];
      }

      if (payload.type === "Incoming") {
        call("mark_as_read", { conversation: conversationName }).catch(() => {});
      }
    };

    statusHandler = (payload) => {
      console.log("[wa-inbox] message_status received:", payload);
      if (!payload) return;
      if (payload.conversation && payload.conversation !== activeConversation.value) return;
      const idx = messages.value.findIndex((m) => m.name === payload.name);
      if (idx !== -1) {
        messages.value[idx].status = payload.status;
        if (payload.error_message) messages.value[idx].error_message = payload.error_message;
      }
    };

    onRealtime("whatsapp_inbox:new_message", newMessageHandler);
    onRealtime("whatsapp_inbox:message_status", statusHandler);
    console.log("[wa-inbox] subscribed to realtime for conversation:", conversationName);
  }

  function unsubscribe() {
    if (newMessageHandler) offRealtime("whatsapp_inbox:new_message", newMessageHandler);
    if (statusHandler) offRealtime("whatsapp_inbox:message_status", statusHandler);
    newMessageHandler = null;
    statusHandler = null;
    activeConversation.value = null;
  }

  async function retryMessage(messageId) {
    sending.value = true;
    try {
      const result = await call("retry_message", { message_id: messageId });
      const idx = messages.value.findIndex((m) => m.name === messageId);
      if (idx !== -1 && result?.status) {
        messages.value[idx].status = result.status;
      }
      return result;
    } finally {
      sending.value = false;
    }
  }

  return {
    messages,
    loading,
    sending,
    hasMore,
    conversationInfo,
    fetchMessages,
    sendReply,
    sendFile,
    loadOlder,
    retryMessage,
    subscribe,
    unsubscribe,
  };
});
