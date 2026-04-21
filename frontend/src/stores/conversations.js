import { defineStore } from "pinia";
import { ref } from "vue";
import { useFrappe } from "@/composables/useFrappe";

export const useConversationsStore = defineStore("conversations", () => {
  const { call, onRealtime, offRealtime } = useFrappe();

  let convUpdateHandler = null;
  let newMessageHandler = null;

  const conversations = ref([]);
  const selected = ref(null);
  const loading = ref(false);
  const filter = ref("all");
  const search = ref("");
  const page = ref(1);
  const hasMore = ref(false);
  const total = ref(0);

  async function fetchConversations(reset = false) {
    if (reset) {
      page.value = 1;
      conversations.value = [];
    }
    loading.value = true;
    try {
      const data = await call("get_conversations", {
        filters: filter.value,
        search: search.value,
        page: page.value,
      });
      if (reset) {
        conversations.value = data.conversations;
      } else {
        conversations.value.push(...data.conversations);
      }
      total.value = data.total;
      hasMore.value = data.has_more;
    } finally {
      loading.value = false;
    }
  }

  function selectConversation(conv) {
    selected.value = conv;
  }

  async function loadMore() {
    if (hasMore.value && !loading.value) {
      page.value++;
      await fetchConversations(false);
    }
  }

  function startRealtime() {
    if (convUpdateHandler) return;

    convUpdateHandler = (payload) => {
      if (!payload?.name) return;
      const idx = conversations.value.findIndex((c) => c.name === payload.name);
      if (idx === -1) {
        conversations.value.unshift({ ...payload });
      } else {
        conversations.value[idx] = { ...conversations.value[idx], ...payload };
        // Move updated conversation to the top
        const [item] = conversations.value.splice(idx, 1);
        conversations.value.unshift(item);
      }
      if (selected.value && selected.value.name === payload.name) {
        selected.value = { ...selected.value, ...payload };
      }
    };

    newMessageHandler = (payload) => {
      if (!payload?.conversation) return;
      const idx = conversations.value.findIndex((c) => c.name === payload.conversation);
      const isActive = selected.value && selected.value.name === payload.conversation;
      const preview = (payload.message || "").slice(0, 100);
      if (idx !== -1) {
        const c = conversations.value[idx];
        c.last_message_at = payload.creation || new Date().toISOString();
        c.last_message_preview = preview;
        c.last_message_type = payload.type;
        if (payload.type === "Incoming" && !isActive) {
          c.unread_count = (c.unread_count || 0) + 1;
        }
        const [item] = conversations.value.splice(idx, 1);
        conversations.value.unshift(item);
      }
    };

    onRealtime("whatsapp_inbox:conversation_update", convUpdateHandler);
    onRealtime("whatsapp_inbox:new_message", newMessageHandler);
  }

  function stopRealtime() {
    if (convUpdateHandler) offRealtime("whatsapp_inbox:conversation_update", convUpdateHandler);
    if (newMessageHandler) offRealtime("whatsapp_inbox:new_message", newMessageHandler);
    convUpdateHandler = null;
    newMessageHandler = null;
  }

  return {
    conversations,
    selected,
    loading,
    filter,
    search,
    page,
    hasMore,
    total,
    fetchConversations,
    selectConversation,
    loadMore,
    startRealtime,
    stopRealtime,
  };
});
