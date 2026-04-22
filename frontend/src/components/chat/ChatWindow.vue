<template>
  <div class="chat-panel" v-if="conversation">
    <!-- Header -->
    <div class="chat-header">
      <div class="chat-header-info">
        <strong>{{ conversation.contact_name || conversation.phone_number }}</strong>
        <span v-if="conversation.contact_name && conversation.contact_name !== conversation.phone_number" class="chat-header-phone">{{ conversation.phone_number }}</span>
      </div>
      <div class="chat-header-status">
        <span class="chat-status-badge" :class="'status-' + conversation.status.toLowerCase()">
          {{ conversation.status }}
        </span>
      </div>
    </div>

    <!-- Lock banner -->
    <div v-if="lockState.locked && !lockState.mine" class="chat-lock-banner locked">
      🔒 هذه المحادثة مع <strong>{{ lockState.holder_name }}</strong> — لا يمكنك الرد
      <button v-if="isAdmin" class="lock-btn" @click="forceRelease">إطلاق القفل</button>
    </div>
    <div v-else-if="lockState.mine" class="chat-lock-banner mine">
      🔓 المحادثة محجوزة لك
      <button class="lock-btn" @click="releaseLock">إطلاق</button>
    </div>

    <!-- Messages -->
    <div class="chat-messages" ref="messagesRef">
      <div v-if="msgStore.loading && msgStore.messages.length === 0" class="chat-loading">
        جاري تحميل الرسائل...
      </div>
      <div v-if="msgStore.hasMore" class="chat-load-more" @click="loadOlder">
        ⬆ تحميل رسائل أقدم
      </div>
      <MessageBubble v-for="m in msgStore.messages" :key="m.name" :msg="m" @retry="onRetry" />
    </div>

    <!-- Reply -->
    <ReplyBox
      :sending="msgStore.sending"
      :disabled="lockState.locked && !lockState.mine"
      :disabled-message="lockDisabledMessage"
      @send="onSend"
      @send-file="onSendFile"
    />
  </div>

  <div class="chat-empty" v-else>
    <div class="chat-empty-icon">💬</div>
    <p>اختر محادثة للبدء</p>
  </div>
</template>

<script setup>
import { watch, ref, nextTick, onMounted, onUnmounted, computed } from 'vue';
import { useConversationsStore } from '@/stores/conversations';
import { useMessagesStore } from '@/stores/messages';
import { useFrappe } from '@/composables/useFrappe';
import MessageBubble from './MessageBubble.vue';
import ReplyBox from './ReplyBox.vue';

const convStore = useConversationsStore();
const msgStore = useMessagesStore();
const { call } = useFrappe();
const messagesRef = ref(null);

const conversation = ref(null);
const lockState = ref({ locked: false, mine: false, holder: null, holder_name: null });

const isAdmin = computed(() => {
  const user = window.frappe?.session?.user;
  const roles = window.frappe?.user_roles || [];
  return user === 'Administrator' || roles.includes('System Manager');
});

const lockDisabledMessage = computed(() => {
  if (lockState.value.locked && !lockState.value.mine) {
    return `🔒 محجوزة مع ${lockState.value.holder_name || ''}`;
  }
  return '';
});

onMounted(() => {
  convStore.startRealtime();
  window.addEventListener('beforeunload', releaseOnExit);
});

onUnmounted(() => {
  msgStore.unsubscribe();
  convStore.stopRealtime();
  window.removeEventListener('beforeunload', releaseOnExit);
  releaseOnExit();
});

watch(() => msgStore.messages.length, () => {
  scrollToBottom();
});

watch(() => convStore.selected, async (conv, prev) => {
  // Release the previous conversation's lock before switching
  if (prev && prev.name && prev.name !== conv?.name) {
    try { await call('release_conversation_lock', { conversation: prev.name }); } catch {}
  }

  if (conv) {
    conversation.value = conv;
    msgStore.unsubscribe();
    await msgStore.fetchMessages(conv.name);
    msgStore.subscribe(conv.name);
    await acquireLock(conv.name);
    scrollToBottom();
  } else {
    msgStore.unsubscribe();
    lockState.value = { locked: false, mine: false };
  }
});

async function acquireLock(name) {
  try {
    const r = await call('acquire_conversation_lock', { conversation: name });
    lockState.value = {
      locked: !!r.locked,
      mine: !!r.mine,
      holder: r.holder,
      holder_name: r.holder_name || r.holder,
    };
  } catch (e) {
    lockState.value = { locked: false, mine: false };
  }
}

async function releaseLock() {
  if (!conversation.value) return;
  try {
    await call('release_conversation_lock', { conversation: conversation.value.name });
    lockState.value = { locked: false, mine: false };
  } catch {}
}

async function forceRelease() {
  if (!conversation.value) return;
  await call('release_conversation_lock', { conversation: conversation.value.name });
  await acquireLock(conversation.value.name);
}

function releaseOnExit() {
  if (conversation.value && lockState.value.mine) {
    // Fire-and-forget — using sendBeacon isn't available for frappe.call
    call('release_conversation_lock', { conversation: conversation.value.name }).catch(() => {});
  }
}

async function onSend(text) {
  if (!conversation.value) return;
  if (lockState.value.locked && !lockState.value.mine) return;
  await msgStore.sendReply(conversation.value.name, text);
  scrollToBottom();
  convStore.fetchConversations(true);
}

async function onSendFile({ file, message }) {
  if (!conversation.value) return;
  if (lockState.value.locked && !lockState.value.mine) return;
  await msgStore.sendFile(conversation.value.name, file, message);
  scrollToBottom();
  convStore.fetchConversations(true);
}

function loadOlder() {
  if (conversation.value) {
    msgStore.loadOlder(conversation.value.name);
  }
}

async function onRetry(msg) {
  if (!msg?.name) return;
  await msgStore.retryMessage(msg.name);
  scrollToBottom();
  convStore.fetchConversations(true);
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
    }
  });
}
</script>

<style scoped>
.chat-lock-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  font-size: 13px;
  border-bottom: 1px solid #eef1f3;
}
.chat-lock-banner.locked {
  background: #fee2e2;
  color: #991b1b;
}
.chat-lock-banner.mine {
  background: #d1fae5;
  color: #065f46;
}
.lock-btn {
  background: #fff;
  border: 1px solid currentColor;
  border-radius: 14px;
  padding: 3px 12px;
  font-size: 11px;
  cursor: pointer;
  color: inherit;
  font-weight: 600;
}
.lock-btn:hover { opacity: 0.85; }
</style>
