<template>
  <div class="msg-row" :class="{ outgoing: isOutgoing, incoming: !isOutgoing }">
    <div class="msg-bubble" :class="{ 'msg-out': isOutgoing, 'msg-in': !isOutgoing }">
      <!-- Sender name -->
      <div v-if="senderName" class="msg-sender" :class="{ 'msg-sender-out': isOutgoing }">
        {{ senderName }}
      </div>

      <!-- Text -->
      <div v-if="msg.content_type === 'text' || !msg.content_type" class="msg-text">
        {{ msg.message }}
      </div>

      <!-- Image -->
      <div v-else-if="msg.content_type === 'image'" class="msg-media">
        <img v-if="msg.attach" :src="msg.attach" class="msg-image" @click="openImage" />
        <div v-else class="msg-placeholder">🖼️ جاري تحميل الصورة...</div>
      </div>

      <!-- Document -->
      <div v-else-if="msg.content_type === 'document'" class="msg-doc">
        <a v-if="msg.attach" :href="msg.attach" target="_blank" class="msg-doc-link">📄 {{ docName }}</a>
        <a v-else-if="msg.reference_doctype && msg.reference_name"
           :href="'/app/' + msg.reference_doctype.toLowerCase().replace(/ /g, '-') + '/' + msg.reference_name"
           target="_blank" class="msg-doc-link">📄 {{ msg.reference_doctype }} - {{ msg.reference_name }}</a>
        <span v-else class="msg-doc-no-link">📄 مستند</span>
      </div>

      <!-- Audio -->
      <div v-else-if="msg.content_type === 'audio'" class="msg-audio">
        <VoiceMessage v-if="msg.attach" :src="msg.attach" :is-outgoing="isOutgoing" :message-id="msg.name" />
        <div v-else class="msg-placeholder">🎤 جاري تحميل الصوت...</div>
      </div>

      <!-- Video -->
      <div v-else-if="msg.content_type === 'video'" class="msg-media">
        <video v-if="msg.attach" :src="msg.attach" controls preload="metadata" class="msg-video"></video>
        <div v-else class="msg-placeholder">🎬 جاري تحميل الفيديو...</div>
      </div>

      <!-- Sticker -->
      <div v-else-if="msg.content_type === 'sticker'" class="msg-media">
        <img :src="msg.attach" class="msg-sticker" @click="openImage" />
      </div>

      <!-- Location -->
      <div v-else-if="msg.content_type === 'location'" class="msg-location">
        <a :href="locationUrl" target="_blank" class="msg-doc-link">📍 {{ msg.message || 'الموقع' }}</a>
      </div>

      <!-- Contact -->
      <div v-else-if="msg.content_type === 'contacts' || msg.content_type === 'contact'" class="msg-doc">
        <span class="msg-doc-no-link">👤 {{ msg.message || 'جهة اتصال' }}</span>
      </div>

      <!-- Reaction -->
      <div v-else-if="msg.content_type === 'reaction'" class="msg-reaction">
        {{ msg.message }}
      </div>

      <!-- Other -->
      <div v-else class="msg-text">{{ msg.message || msg.content_type }}</div>

      <!-- Time + Status -->
      <div class="msg-footer">
        <span class="msg-time">{{ formattedTime }}</span>
        <span v-if="isOutgoing && isFailed" class="msg-retry" @click="onRetryClick" :title="msg.error_message || 'إعادة الإرسال'">
          ⚠ إعادة
        </span>
        <span v-else-if="isOutgoing" class="msg-status">
          {{ msg.status === 'read' ? '✓✓' : msg.status === 'delivered' ? '✓✓' : '✓' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import VoiceMessage from './VoiceMessage.vue';

const props = defineProps({ msg: Object });
const emit = defineEmits(['retry']);

const isFailed = computed(() => {
  const s = (props.msg.status || '').toLowerCase();
  return s === 'failed' || s === 'error';
});

const isOutgoing = computed(() => props.msg.type === 'Outgoing');

const senderName = computed(() => {
  const s = props.msg.sender_name;
  return s && s !== 'Guest' ? s : '';
});

const docName = computed(() => {
  if (!props.msg.attach) return 'مستند';
  try {
    const decoded = decodeURIComponent(props.msg.attach.split('/').pop());
    return decoded || 'مستند';
  } catch { return props.msg.attach.split('/').pop() || 'مستند'; }
});

const formattedTime = computed(() => {
  if (!props.msg.creation) return '';
  const d = new Date(props.msg.creation);
  return d.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
});

const locationUrl = computed(() => {
  const m = props.msg.message || '';
  const match = m.match(/(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)/);
  if (match) return `https://www.google.com/maps?q=${match[1]},${match[2]}`;
  return 'https://www.google.com/maps';
});

function openImage() {
  window.open(props.msg.attach, '_blank');
}

function onRetryClick() {
  emit('retry', props.msg);
}
</script>

<style scoped>
.msg-retry {
  font-size: 11px;
  color: #c0392b;
  cursor: pointer;
  font-weight: 600;
}
.msg-retry:hover { text-decoration: underline; }
.msg-sender {
  font-size: 12px;
  font-weight: 600;
  color: #d97706;
  margin-bottom: 2px;
  line-height: 1.2;
}
.msg-sender-out { color: #0d9488; }

.msg-video {
  max-width: 280px;
  max-height: 320px;
  border-radius: 8px;
  display: block;
  margin: 2px 0;
  background: #000;
}
.msg-sticker {
  max-width: 150px;
  max-height: 150px;
  cursor: pointer;
  background: transparent;
}
.msg-location {
  padding: 8px 12px;
  background: rgba(0,0,0,0.04);
  border-radius: 6px;
  margin: 2px 0;
}
.msg-reaction {
  font-size: 36px;
  line-height: 1;
}

.msg-placeholder {
  padding: 16px 20px;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  font-size: 13px;
  color: #667781;
  font-style: italic;
  text-align: center;
  min-width: 180px;
}
</style>
