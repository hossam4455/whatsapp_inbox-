<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal">
      <header class="m-head">
        <div>
          <h3 class="m-title">{{ data?.title || campaignName }}</h3>
          <div class="m-sub">
            <span class="m-badge" :class="statusClass">{{ statusLabel }}</span>
            <span class="m-tpl">القالب: {{ data?.template || '—' }}</span>
          </div>
        </div>
        <button class="m-close" @click="$emit('close')">✕</button>
      </header>

      <div v-if="loading" class="m-loading">جاري التحميل...</div>

      <div v-else-if="data" class="m-body">
        <!-- Summary cells -->
        <div class="cells">
          <div class="cell neutral">
            <div class="cv">{{ data.stats.targets }}</div>
            <div class="cl">المستهدفون</div>
          </div>
          <div class="cell purple">
            <div class="cv">{{ data.stats.processed }}</div>
            <div class="cl">أُرسل</div>
          </div>
          <div class="cell green">
            <div class="cv">{{ data.stats.delivered }}</div>
            <div class="cl">{{ pct(data.stats.delivered, data.stats.targets) }}%</div>
            <div class="cs">وصل</div>
          </div>
          <div class="cell blue">
            <div class="cv">{{ data.stats.read }}</div>
            <div class="cl">{{ pct(data.stats.read, data.stats.targets) }}%</div>
            <div class="cs">قُرئ</div>
          </div>
          <div class="cell red">
            <div class="cv">{{ data.stats.failed }}</div>
            <div class="cl">{{ pct(data.stats.failed, data.stats.targets) }}%</div>
            <div class="cs">فشل</div>
          </div>
        </div>

        <div class="progress-bar">
          <span class="seg red" :style="{ width: pct(data.stats.failed, data.stats.targets) + '%' }"></span>
          <span class="seg blue" :style="{ width: pct(data.stats.read, data.stats.targets) + '%' }"></span>
          <span class="seg green" :style="{ width: pct(data.stats.delivered, data.stats.targets) + '%' }"></span>
        </div>
        <div class="progress-legend">
          <span class="g">● وصل: {{ pct(data.stats.delivered, data.stats.targets) }}%</span>
          <span class="b">● قُرئ: {{ pct(data.stats.read, data.stats.targets) }}%</span>
          <span class="r">● فشل: {{ pct(data.stats.failed, data.stats.targets) }}%</span>
        </div>

        <div class="meta">
          أُرسل = قبلته ميتا | وصل = وصل للهاتف | قُرئ = فُتح
        </div>

        <!-- Campaign metadata -->
        <div class="info-row">
          <span><strong>انتهت:</strong> {{ fmtDate(data.modified) }}</span>
          <span><strong>بدأت:</strong> {{ fmtDate(data.creation) }}</span>
          <span v-if="data.scheduled_time"><strong>مجدولة:</strong> {{ fmtDate(data.scheduled_time) }}</span>
          <span><strong>رقم الإرسال:</strong> {{ data.from_number || '—' }}</span>
        </div>

        <!-- Recipients section -->
        <section class="block">
          <h4>🎯 المستهدفون ({{ data.recipients.length }})</h4>
          <ul class="rec-list">
            <li v-for="r in data.recipients" :key="r.mobile_number">
              <span>{{ r.mobile_number }}</span>
              <span class="muted">{{ r.recipient_name || '—' }}</span>
              <span class="ok-chip">✓ تم الإرسال</span>
            </li>
            <li v-if="!data.recipients.length" class="empty">لا توجد قائمة مستهدفين محفوظة</li>
          </ul>
        </section>

        <!-- Events -->
        <section class="block">
          <header class="block-head">
            <h4>📋 المستلمون والتتبع</h4>
            <button class="btn-ghost small" @click="reload">↻ تحديث</button>
          </header>

          <div class="subtabs">
            <button class="subtab active">المستلمون</button>
            <button class="subtab">سجل التسليم</button>
            <button class="subtab">النشاط</button>
          </div>

          <div class="event-chips">
            <button
              v-for="c in eventChips" :key="c.id"
              class="chip"
              :class="{ active: eventFilter === c.id }"
              @click="eventFilter = c.id"
            >{{ c.label }} ({{ eventCount(c.id) }})</button>
          </div>

          <input type="text" v-model="search" placeholder="🔍 ابحث برقم الهاتف..." class="search-input" />

          <div class="event-count">عرض {{ filteredEvents.length }} من {{ data.messages.length }}</div>

          <ul class="event-list">
            <li v-for="m in filteredEvents" :key="m.name" class="event-item">
              <div class="evt-head">
                <div>
                  <strong>{{ m.to }}</strong>
                  <div class="evt-time">إرسال: {{ fmtDate(m.creation) }} · آخر محاولة: {{ fmtDate(m.creation) }}</div>
                </div>
                <button class="btn-ghost small">↩ سجل</button>
              </div>
              <div class="evt-body">
                <span v-if="m.message_id" class="muted">#{{ m.message_id.slice(0, 10) }}</span>
                <span v-if="m.message" class="evt-msg">{{ m.message.slice(0, 120) }}</span>
                <span class="status-chip" :class="statusChipClass(m.status)">
                  {{ statusChipLabel(m.status) }}
                </span>
              </div>
              <div v-if="m.error_message" class="evt-error">⚠ {{ m.error_message }}</div>
            </li>
            <li v-if="!filteredEvents.length" class="empty">لا توجد أحداث تطابق.</li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useFrappe } from '@/composables/useFrappe';

const props = defineProps({ campaignName: String });
defineEmits(['close']);

const { call } = useFrappe();

const data = ref(null);
const loading = ref(false);
const eventFilter = ref('all');
const search = ref('');

const eventChips = [
  { id: 'all', label: 'الكل' },
  { id: 'delivered', label: 'وصل' },
  { id: 'read', label: 'قُرئ' },
  { id: 'sent', label: 'أُرسل' },
  { id: 'failed', label: 'فشل' },
];

const statusClass = computed(() => {
  const x = (data.value?.status || '').toLowerCase();
  if (x === 'completed') return 'ok';
  if (x === 'in progress' || x === 'queued') return 'progress';
  if (x === 'cancelled' || x === 'partially failed') return 'danger';
  return 'neutral';
});
const statusLabel = computed(() => {
  const m = { 'Completed': 'مكتملة', 'In Progress': 'جارية', 'Queued': 'مجدولة',
              'Draft': 'مسودة', 'Partially Failed': 'فشل جزئي', 'Cancelled': 'ملغاة' };
  return m[data.value?.status] || data.value?.status || '—';
});

const filteredEvents = computed(() => {
  let msgs = data.value?.messages || [];
  if (search.value) msgs = msgs.filter(m => (m.to || '').includes(search.value));
  if (eventFilter.value !== 'all') {
    msgs = msgs.filter(m => matchStatus(m.status, eventFilter.value));
  }
  return msgs;
});

function matchStatus(s, f) {
  const x = (s || '').toLowerCase();
  if (f === 'delivered') return x === 'delivered' || x === 'sent' || x === 'success';
  if (f === 'read') return x === 'read';
  if (f === 'sent') return x === 'sent' || x === 'success';
  if (f === 'failed') return x === 'failed' || x === 'error';
  return true;
}
function eventCount(f) {
  const msgs = data.value?.messages || [];
  if (f === 'all') return msgs.length;
  return msgs.filter(m => matchStatus(m.status, f)).length;
}

function statusChipClass(s) {
  const x = (s || '').toLowerCase();
  if (x === 'read') return 'blue';
  if (x === 'delivered' || x === 'success' || x === 'sent') return 'green';
  if (x === 'failed' || x === 'error') return 'red';
  return 'neutral';
}
function statusChipLabel(s) {
  const m = { 'read': '👁 قُرئ', 'delivered': '✓ وصل', 'sent': '✓ أُرسل', 'success': '✓ وصل', 'failed': '✗ فشل', 'error': '✗ خطأ' };
  return m[(s || '').toLowerCase()] || s || '—';
}

function pct(n, d) { return d ? Math.round((n / d) * 100) : 0; }
function fmtDate(d) {
  if (!d) return '—';
  try { return new Date(d).toLocaleString('ar-SA'); }
  catch { return d; }
}

async function reload() {
  loading.value = true;
  try {
    data.value = await call('get_campaign_detail', { campaign: props.campaignName });
  } finally { loading.value = false; }
}

onMounted(reload);
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal {
  background: #fff;
  border-radius: 14px;
  width: 100%;
  max-width: 780px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
}

.m-head {
  padding: 18px 22px;
  border-bottom: 1px solid #eef1f3;
  display: flex;
  justify-content: space-between;
  align-items: start;
}
.m-title { margin: 0; font-size: 18px; font-weight: 700; }
.m-sub { margin-top: 6px; display: flex; gap: 10px; align-items: center; font-size: 12px; }
.m-tpl { color: #667781; }
.m-badge { padding: 2px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.m-badge.ok { background: #d1fae5; color: #065f46; }
.m-badge.progress { background: #fef3c7; color: #92400e; }
.m-badge.danger { background: #fee2e2; color: #991b1b; }
.m-badge.neutral { background: #f1f5f9; color: #475569; }

.m-close {
  background: none; border: none; font-size: 20px; cursor: pointer;
  color: #98a2a7; padding: 0 4px;
}
.m-close:hover { color: #111b21; }

.m-loading { padding: 60px; text-align: center; color: #667781; }
.m-body { padding: 22px; display: flex; flex-direction: column; gap: 18px; }

.cells {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}
@media (max-width: 680px) { .cells { grid-template-columns: 1fr 1fr 1fr; } }
.cell {
  border-radius: 10px;
  padding: 14px 10px;
  text-align: center;
  border: 1px solid #eef1f3;
}
.cell.neutral { background: #f8fafb; }
.cell.purple { background: #f5f3ff; }
.cell.green { background: #ecf7ee; }
.cell.blue { background: #eaf2fb; }
.cell.red { background: #fef2f3; }
.cell .cv { font-size: 22px; font-weight: 700; }
.cell.neutral .cv { color: #111b21; }
.cell.purple .cv { color: #7c3aed; }
.cell.green .cv { color: #10b981; }
.cell.blue .cv { color: #2563eb; }
.cell.red .cv { color: #dc2626; }
.cell .cl { font-size: 12px; color: #3b4a54; margin-top: 4px; font-weight: 600; }
.cell .cs { font-size: 10px; color: #667781; }

.progress-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  background: #e5e7eb;
}
.progress-bar .seg.green { background: #10b981; }
.progress-bar .seg.blue { background: #2563eb; }
.progress-bar .seg.red { background: #dc2626; }
.progress-legend {
  display: flex; justify-content: center; gap: 16px;
  font-size: 11px; font-weight: 600;
}
.progress-legend .g { color: #10b981; }
.progress-legend .b { color: #2563eb; }
.progress-legend .r { color: #dc2626; }

.meta {
  text-align: center;
  font-size: 11px;
  color: #667781;
  background: #f8fafb;
  padding: 6px;
  border-radius: 6px;
}

.info-row {
  display: flex; flex-wrap: wrap; gap: 14px;
  font-size: 12px; color: #3b4a54;
  background: #f8fafb;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #eef1f3;
}
.info-row strong { color: #667781; font-weight: 600; }

.block {
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 14px;
}
.block h4 { margin: 0 0 10px; font-size: 14px; }
.block-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }

.rec-list, .event-list {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 8px;
}
.rec-list li {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafb;
  border-radius: 6px;
  font-size: 13px;
}
.muted { color: #98a2a7; }
.ok-chip { background: #d1fae5; color: #065f46; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }

.subtabs { display: flex; gap: 4px; margin-bottom: 10px; }
.subtab {
  background: #fff;
  border: 1px solid #e0e5e7;
  padding: 5px 12px;
  border-radius: 14px;
  font-size: 12px;
  cursor: pointer;
  color: #3b4a54;
}
.subtab.active { background: #f59e0b; color: #fff; border-color: #f59e0b; }

.event-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.chip {
  background: #fff;
  border: 1px solid #e0e5e7;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 11px;
  cursor: pointer;
  color: #3b4a54;
}
.chip.active { background: #1a1f22; color: #fff; border-color: #1a1f22; }

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e0e5e7;
  border-radius: 18px;
  font-size: 12px;
  margin-bottom: 10px;
}

.event-count { font-size: 11px; color: #667781; margin-bottom: 10px; }

.event-item {
  padding: 12px;
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 8px;
}
.evt-head { display: flex; justify-content: space-between; align-items: start; margin-bottom: 6px; }
.evt-time { font-size: 11px; color: #98a2a7; margin-top: 2px; }
.evt-body { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: 12px; }
.evt-msg { color: #3b4a54; }

.status-chip { padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: 600; }
.status-chip.green { background: #d1fae5; color: #065f46; }
.status-chip.blue { background: #dbeafe; color: #1e40af; }
.status-chip.red { background: #fee2e2; color: #991b1b; }
.status-chip.neutral { background: #f1f5f9; color: #475569; }

.evt-error {
  margin-top: 6px;
  padding: 6px 10px;
  background: #fef2f3;
  color: #991b1b;
  border-radius: 6px;
  font-size: 12px;
}

.btn-ghost {
  background: #fff;
  border: 1px solid #e0e5e7;
  border-radius: 16px;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  color: #3b4a54;
}
.btn-ghost.small { padding: 4px 10px; font-size: 11px; }
.btn-ghost:hover { background: #f3f5f6; }

.empty { padding: 20px; text-align: center; color: #98a2a7; font-size: 12px; }
</style>
