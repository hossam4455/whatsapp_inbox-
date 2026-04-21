<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal">
      <header class="m-head">
        <div>
          <h3 class="m-title">{{ template.template_name || template.name }}</h3>
          <div class="m-sub">
            <span><strong>الاسم:</strong> {{ template.actual_name || template.name }}</span>
            <span><strong>الحالة:</strong>
              <span class="chip-status" :class="statusClass">{{ statusLabel }}</span>
            </span>
          </div>
        </div>
        <button class="m-close" @click="$emit('close')">✕</button>
      </header>

      <div class="m-body">
        <!-- Name variations preview -->
        <div class="names-row">
          <span class="label">معاينة كـ:</span>
          <button
            v-for="n in names" :key="n"
            class="name-chip"
            :class="{ active: activeName === n }"
            @click="activeName = n"
          >{{ n }}</button>
        </div>

        <!-- WhatsApp phone mock -->
        <div class="phone-frame">
          <div class="phone-top">
            <span class="phone-time">{{ currentTime }}</span>
            <span class="phone-indicators">🔋 📶 📡</span>
          </div>
          <div class="phone-header">
            <span class="phone-avatar">✓</span>
            <div>
              <div class="phone-name">{{ template.header || 'Business' }}</div>
              <div class="phone-status">متصل</div>
            </div>
          </div>
          <div class="phone-chat">
            <div class="bubble">
              <div v-if="template.header" class="bubble-header">{{ renderVariables(template.header) }}</div>
              <div class="bubble-body">{{ renderVariables(bodyText) }}</div>
              <div v-if="template.footer" class="bubble-footer">{{ template.footer }}</div>
              <div class="bubble-time">{{ currentTime }} ✓✓</div>
            </div>
          </div>
        </div>

        <div class="actions-row">
          <button class="btn-dark" @click="useAsBase">📋 استخدم كأساس لقالب جديد</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({ template: Object });
defineEmits(['close']);

const names = ['أحمد', 'سارة', 'عميل', 'خالد'];
const activeName = ref('أحمد');

const bodyText = computed(() => {
  return props.template.template || props.template.message || 'Hello World';
});

const currentTime = computed(() => {
  return new Date().toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
});

const statusClass = computed(() => {
  const s = (props.template.status || '').toLowerCase();
  if (s === 'approved') return 'ok';
  if (s === 'pending' || s === 'in review') return 'progress';
  if (s === 'rejected') return 'danger';
  return 'neutral';
});
const statusLabel = computed(() => {
  const m = { 'approved': 'معتمد', 'pending': 'قيد المراجعة', 'in review': 'قيد المراجعة', 'rejected': 'مرفوض' };
  return m[(props.template.status || '').toLowerCase()] || props.template.status || '—';
});

function renderVariables(text) {
  if (!text) return '';
  return text
    .replace(/\{\{\s*1\s*\}\}/g, activeName.value)
    .replace(/\{\{\s*name\s*\}\}/gi, activeName.value);
}

function useAsBase() {
  window.open('/app/whatsapp-templates/new?copy_from=' + encodeURIComponent(props.template.name), '_blank');
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.modal {
  background: #fff;
  border-radius: 14px;
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.m-head {
  padding: 16px 20px;
  border-bottom: 1px solid #eef1f3;
  display: flex;
  justify-content: space-between;
  align-items: start;
}
.m-title { margin: 0; font-size: 16px; }
.m-sub { margin-top: 6px; display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; color: #3b4a54; }
.m-close { background: none; border: none; font-size: 20px; cursor: pointer; color: #98a2a7; }

.chip-status { padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.chip-status.ok { background: #d1fae5; color: #065f46; }
.chip-status.progress { background: #fef3c7; color: #92400e; }
.chip-status.danger { background: #fee2e2; color: #991b1b; }
.chip-status.neutral { background: #f1f5f9; color: #475569; }

.m-body { padding: 20px; display: flex; flex-direction: column; gap: 14px; }

.names-row { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.label { font-size: 12px; color: #667781; margin-inline-end: 6px; }
.name-chip {
  background: #fff;
  border: 1px solid #e0e5e7;
  border-radius: 14px;
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  color: #3b4a54;
}
.name-chip.active {
  background: #d1fae5;
  color: #065f46;
  border-color: #10b981;
}

.phone-frame {
  background: #222;
  border-radius: 24px;
  padding: 8px;
  margin: 0 auto;
  max-width: 280px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.15);
}
.phone-top {
  color: #fff;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  padding: 4px 12px;
}
.phone-header {
  background: #075e54;
  color: #fff;
  padding: 10px;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.phone-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: #10b981; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px;
}
.phone-name { font-size: 13px; font-weight: 600; }
.phone-status { font-size: 10px; opacity: 0.8; }

.phone-chat {
  background: #ece5dd;
  min-height: 200px;
  padding: 16px 12px;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
}
.bubble {
  background: #dcf8c6;
  padding: 8px 10px;
  border-radius: 8px;
  max-width: 85%;
  margin-inline-start: auto;
  font-size: 13px;
  line-height: 1.5;
  color: #111b21;
  box-shadow: 0 1px 1px rgba(0,0,0,0.1);
}
.bubble-header { font-weight: 700; margin-bottom: 4px; }
.bubble-body { white-space: pre-wrap; }
.bubble-footer { font-size: 11px; color: #667781; margin-top: 4px; }
.bubble-time { font-size: 10px; color: #667781; text-align: left; margin-top: 4px; }

.actions-row { display: flex; justify-content: center; }
.btn-dark {
  background: #1a1f22;
  color: #fff;
  border: none;
  border-radius: 18px;
  padding: 8px 16px;
  font-size: 12px;
  cursor: pointer;
}
.btn-dark:hover { background: #2d3336; }
</style>
