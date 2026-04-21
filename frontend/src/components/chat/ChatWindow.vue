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
    <ReplyBox :sending="msgStore.sending" @send="onSend" @send-file="onSendFile" />
  </div>

  <div class="chat-empty" v-else>
    <div class="chat-empty-icon">💬</div>
    <p>اختر محادثة للبدء</p>
  </div>
</template>

<script setup>
import { watch, ref, nextTick, onMounted, onUnmounted } from 'vue';
import { useConversationsStore } from '@/stores/conversations';
import { useMessagesStore } from '@/stores/messages';
import MessageBubble from './MessageBubble.vue';
import ReplyBox from './ReplyBox.vue';

const convStore = useConversationsStore();
const msgStore = useMessagesStore();
const messagesRef = ref(null);

const conversation = ref(null);

onMounted(() => {
  convStore.startRealtime();
});

onUnmounted(() => {
  msgStore.unsubscribe();
  convStore.stopRealtime();
});

watch(() => msgStore.messages.length, () => {
  scrollToBottom();
});

watch(() => convStore.selected, async (conv) => {
  if (conv) {
    conversation.value = conv;
    msgStore.unsubscribe();
    await msgStore.fetchMessages(conv.name);
    msgStore.subscribe(conv.name);
    scrollToBottom();
  } else {
    msgStore.unsubscribe();
  }
});

async function onSend(text) {
  if (!conversation.value) return;
  await msgStore.sendReply(conversation.value.name, text);
  scrollToBottom();
  convStore.fetchConversations(true);
}

async function onSendFile({ file, message }) {
  if (!conversation.value) return;
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
