<template>
  <div
    class="conv-item"
    :class="{ active: isSelected, unread: conv.unread_count > 0 }"
    @click="$emit('select', conv)"
  >
    <!-- Avatar -->
    <div class="conv-avatar" :class="avatarColor">
      {{ initial }}
    </div>

    <!-- Main content -->
    <div class="conv-body">
      <!-- Row 1: Name + Time -->
      <div class="conv-row-1">
        <span class="conv-name">{{ conv.contact_name || conv.phone_number }}</span>
        <span class="conv-time">{{ timeAgo }}</span>
      </div>

      <!-- Row 2: Status + Assigned -->
      <div class="conv-row-2">
        <span class="conv-status-pill" :class="'pill-' + conv.status.toLowerCase()">
          {{ statusLabel }}
        </span>
        <span v-if="conv.assigned_name" class="conv-assigned-tag">
          مسند إلى: {{ conv.assigned_name }}
        </span>
      </div>

      <!-- Row 3: Preview -->
      <div class="conv-row-3">
        <span class="conv-preview-text">{{ previewText }}</span>
        <span v-if="conv.unread_count > 0" class="conv-badge">{{ conv.unread_count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  conv: Object,
  isSelected: Boolean,
});

defineEmits(['select']);

const initial = computed(() => {
  const name = props.conv.contact_name || props.conv.phone_number || '';
  // For Arabic names, take first char; for numbers, take last 2 digits
  if (/^\d/.test(name)) return name.slice(-2);
  return name.charAt(0);
});

const avatarColor = computed(() => {
  const colors = ['av-green', 'av-blue', 'av-orange', 'av-purple', 'av-teal', 'av-pink'];
  const hash = (props.conv.phone_number || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return colors[hash % colors.length];
});

const statusLabel = computed(() => {
  const map = { Active: 'نشط', Pending: 'بانتظار', Replied: 'تم الرد', Escalated: 'متأخر', Closed: 'مغلق' };
  return map[props.conv.status] || props.conv.status;
});

const previewText = computed(() => {
  const p = props.conv.last_message_preview || '';
  const prefix = props.conv.last_message_type === 'Outgoing' ? 'أنت: ' : '';
  return prefix + p;
});

const timeAgo = computed(() => {
  if (!props.conv.last_message_at) return '';
  const d = new Date(props.conv.last_message_at);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return 'الآن';
  if (diff < 3600) return Math.floor(diff / 60) + ' د';
  if (diff < 86400) return Math.floor(diff / 3600) + ' س';
  if (diff < 172800) return 'أمس';
  return d.toLocaleDateString('ar-SA');
});
</script>
