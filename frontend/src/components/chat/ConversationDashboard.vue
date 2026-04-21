<template>
  <div v-if="conversation" class="conv-dashboard">
    <!-- Toolbar -->
    <div class="dash-toolbar">
      <button class="dash-btn dark" @click="$emit('hide')">إخفاء اللوحة</button>
      <button class="dash-btn" @click="autoAssign" :disabled="busy">تعيين تلقائي</button>
      <button class="dash-btn" @click="linkCustomer">ربط عميل</button>
      <button class="dash-btn" @click="resetAssignment" :disabled="busy">إعادة تعيين</button>
    </div>

    <div class="dash-section">
      <div class="dash-title">لوحة المحادثة</div>

      <!-- 24h window -->
      <div class="dash-window" :class="windowClass">
        <span v-if="windowOpen">نافذة الرد مفتوحة <strong>{{ windowRemaining }}</strong> متبقية</span>
        <span v-else>نافذة الرد مغلقة — استخدم قالباً</span>
      </div>

      <!-- Top stats row -->
      <div class="dash-grid">
        <div class="dash-cell">
          <div class="dash-label">الأولوية</div>
          <div class="dash-value">{{ priorityScore }}</div>
        </div>
        <div class="dash-cell">
          <div class="dash-label">غير مقروء</div>
          <div class="dash-value">{{ stats.unread_count || 0 }}</div>
        </div>
      </div>

      <div class="dash-grid">
        <div class="dash-cell">
          <div class="dash-label">الانتظار</div>
          <div class="dash-value">{{ waitingOn }}</div>
        </div>
        <div class="dash-cell">
          <div class="dash-label">جاهزية العميل</div>
          <div class="dash-value" :class="readinessClass">{{ readiness }}</div>
        </div>
      </div>

      <!-- Classification -->
      <div class="dash-row">
        <div class="dash-label">نوع المحادثة</div>
        <div class="dash-pills">
          <button
            v-for="c in categories" :key="c.value"
            class="dash-pill"
            :class="{ active: category === c.value }"
            @click="setCategory(c.value)"
          >
            <span v-if="c.icon">{{ c.icon }}</span> {{ c.label }}
          </button>
        </div>
      </div>

      <!-- Follow-up -->
      <div class="dash-status" :class="{ neutral: !needsFollowup, warn: needsFollowup }">
        {{ needsFollowup ? '⚑ يحتاج متابعة' : '✓ لا تحتاج متابعة' }}
      </div>

      <div class="dash-meta">ثقة التصنيف: <strong>{{ classificationConfidence }}%</strong></div>
    </div>

    <!-- Activity -->
    <div class="dash-section">
      <div class="dash-subtitle">آخر رد من: <strong>{{ lastReplyFrom }}</strong></div>
      <ul class="dash-list">
        <li><span>رسائل العميل</span><strong>{{ stats.incoming_count || 0 }}</strong></li>
        <li><span>رسائل الموظف</span><strong>{{ stats.outgoing_count || 0 }}</strong></li>
        <li><span>آخر رسالة</span><strong>{{ timeSinceLast }}</strong></li>
      </ul>
    </div>

    <!-- Assignment -->
    <div class="dash-section">
      <div class="dash-subtitle">المسؤول</div>
      <div class="dash-assigned">
        <span v-if="stats.assigned_name">{{ stats.assigned_name }}</span>
        <span v-else class="dash-muted">غير معيّن</span>
      </div>
      <textarea
        v-model="notes"
        @blur="saveNotes"
        placeholder="ملاحظات داخلية..."
        class="dash-notes"
        rows="3"
        dir="auto"
      ></textarea>
    </div>
  </div>
  <div v-else class="conv-dashboard empty">
    <span class="dash-muted">اختر محادثة لعرض اللوحة</span>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useConversationsStore } from '@/stores/conversations';
import { useFrappe } from '@/composables/useFrappe';

defineEmits(['hide']);

const convStore = useConversationsStore();
const { call, onRealtime, offRealtime } = useFrappe();

const stats = ref({});
const busy = ref(false);
const notes = ref('');
const category = ref('potential');
const needsFollowup = ref(false);
const now = ref(Date.now());
let tickTimer = null;
let realtimeHandler = null;

const conversation = computed(() => convStore.selected);

const categories = [
  { value: 'potential', label: 'عميل محتمل', icon: '👤' },
  { value: 'vendor', label: 'مزود خدمة', icon: '❓' },
  { value: 'other', label: 'أخرى', icon: '' },
];

const windowMs = computed(() => {
  if (!stats.value.last_incoming_at) return 0;
  const t = new Date(stats.value.last_incoming_at).getTime();
  const remaining = t + 24 * 3600 * 1000 - now.value;
  return Math.max(0, remaining);
});
const windowOpen = computed(() => windowMs.value > 0);
const windowClass = computed(() => {
  if (!windowOpen.value) return 'danger';
  if (windowMs.value < 2 * 3600 * 1000) return 'warn';
  return 'ok';
});
const windowRemaining = computed(() => {
  const ms = windowMs.value;
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return h + 'h ' + m + 'm';
});

const priorityScore = computed(() => {
  const p = (stats.value.priority || '').toString().toLowerCase();
  if (p.includes('high') || p.includes('عالي')) return 85;
  if (p.includes('medium') || p.includes('متوسط')) return 50;
  if (p.includes('low') || p.includes('منخفض')) return 20;
  return 50;
});

const waitingOn = computed(() => {
  if (!stats.value.last_message_type) return '—';
  return stats.value.last_message_type === 'Incoming' ? 'الموظف' : 'العميل';
});

const readiness = computed(() => {
  const inC = stats.value.incoming_count || 0;
  const outC = stats.value.outgoing_count || 0;
  if (inC >= 5 && outC >= 3) return 'عالية';
  if (inC >= 2) return 'متوسطة';
  return 'منخفضة';
});
const readinessClass = computed(() => ({
  'good': readiness.value === 'عالية',
  'warn': readiness.value === 'متوسطة',
  'muted': readiness.value === 'منخفضة',
}));

const classificationConfidence = computed(() => {
  const total = (stats.value.incoming_count || 0) + (stats.value.outgoing_count || 0);
  return Math.min(99, 50 + Math.min(total, 20) * 2.5).toFixed(0);
});

const lastReplyFrom = computed(() => {
  if (stats.value.last_message_type === 'Outgoing') return stats.value.assigned_name || 'الموظف';
  return stats.value.contact_name || stats.value.phone_number || 'العميل';
});

const timeSinceLast = computed(() => {
  if (!stats.value.last_message_at) return '—';
  const diff = now.value - new Date(stats.value.last_message_at).getTime();
  if (diff < 60000) return 'الآن';
  if (diff < 3600000) return Math.floor(diff / 60000) + ' د';
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' س';
  return Math.floor(diff / 86400000) + ' ي';
});

async function loadStats() {
  if (!conversation.value) {
    stats.value = {};
    return;
  }
  try {
    const data = await call('get_conversation_stats', { conversation: conversation.value.name });
    stats.value = data || {};
    notes.value = data?.internal_notes || '';
    const tag = (data?.tags_list || '').toString().toLowerCase();
    if (tag.includes('follow')) needsFollowup.value = true;
  } catch {}
}

watch(conversation, loadStats, { immediate: true });

onMounted(() => {
  tickTimer = setInterval(() => { now.value = Date.now(); }, 30000);
  realtimeHandler = (payload) => {
    if (!payload || !conversation.value) return;
    if (payload.name === conversation.value.name || payload.conversation === conversation.value.name) {
      loadStats();
    }
  };
  onRealtime('whatsapp_inbox:conversation_update', realtimeHandler);
  onRealtime('whatsapp_inbox:new_message', realtimeHandler);
});

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer);
  if (realtimeHandler) {
    offRealtime('whatsapp_inbox:conversation_update', realtimeHandler);
    offRealtime('whatsapp_inbox:new_message', realtimeHandler);
  }
});

async function saveNotes() {
  if (!conversation.value) return;
  try {
    await call('update_conversation', {
      conversation: conversation.value.name,
      internal_notes: notes.value,
    });
  } catch {}
}

async function autoAssign() {
  if (!conversation.value) return;
  busy.value = true;
  try {
    // Simple: assign to current user
    const me = window.frappe?.session?.user;
    if (me) {
      await call('update_conversation', { conversation: conversation.value.name, assigned_to: me });
      await loadStats();
    }
  } finally { busy.value = false; }
}

async function resetAssignment() {
  if (!conversation.value) return;
  busy.value = true;
  try {
    await call('update_conversation', { conversation: conversation.value.name, assigned_to: '' });
    await loadStats();
  } finally { busy.value = false; }
}

function linkCustomer() {
  if (!conversation.value) return;
  const phone = conversation.value.phone_number || '';
  window.open('/app/customer/view/list?mobile_no=' + encodeURIComponent(phone), '_blank');
}

async function setCategory(v) {
  category.value = v;
}
</script>

<style scoped>
.conv-dashboard {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background: #fff;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 12px;
  font-size: 13px;
  color: #111b21;
}
.conv-dashboard.empty {
  align-items: center;
  justify-content: center;
}
.dash-muted { color: #98a2a7; }

.dash-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.dash-btn {
  background: #fff;
  border: 1px solid #e0e5e7;
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s;
  color: #333;
}
.dash-btn:hover { background: #f3f5f6; }
.dash-btn.dark { background: #1a1f22; color: #fff; border-color: #1a1f22; }
.dash-btn:disabled { opacity: 0.5; cursor: wait; }

.dash-section {
  background: #f8fafb;
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.dash-title {
  font-size: 15px;
  font-weight: 700;
  color: #111b21;
}
.dash-subtitle {
  font-size: 13px;
  color: #3b4a54;
}

.dash-window {
  text-align: center;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}
.dash-window.ok { background: #e6f7ef; color: #067a46; }
.dash-window.warn { background: #fff4e0; color: #a15a00; }
.dash-window.danger { background: #fde8ea; color: #a41724; }

.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.dash-cell {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}
.dash-label { font-size: 11px; color: #667781; margin-bottom: 4px; }
.dash-value { font-size: 16px; font-weight: 700; color: #111b21; }
.dash-value.good { color: #067a46; }
.dash-value.warn { color: #a15a00; }
.dash-value.muted { color: #98a2a7; }

.dash-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dash-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.dash-pill {
  background: #fff;
  border: 1px solid #e0e5e7;
  border-radius: 20px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.dash-pill:hover { background: #f3f5f6; }
.dash-pill.active {
  background: #00a884;
  color: #fff;
  border-color: #00a884;
}

.dash-status {
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 12px;
}
.dash-status.neutral { background: #e6f7ef; color: #067a46; }
.dash-status.warn { background: #fff4e0; color: #a15a00; }

.dash-meta { font-size: 12px; color: #0088cc; }

.dash-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dash-list li {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #3b4a54;
}
.dash-list li strong { color: #111b21; font-weight: 600; }

.dash-assigned {
  padding: 8px 10px;
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 6px;
  font-size: 13px;
}
.dash-notes {
  width: 100%;
  resize: vertical;
  padding: 8px;
  border: 1px solid #e0e5e7;
  border-radius: 6px;
  font-family: inherit;
  font-size: 12px;
}
.dash-notes:focus { outline: none; border-color: #00a884; }
</style>
