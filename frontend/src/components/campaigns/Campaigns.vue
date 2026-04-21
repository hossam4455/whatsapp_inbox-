<template>
  <div class="cmp-root">
    <!-- Mode toggle: campaigns / templates -->
    <div class="cmp-mode-row">
      <div class="cmp-mode-toggle">
        <button
          class="mode-btn"
          :class="{ active: mode === 'templates' }"
          @click="mode = 'templates'"
        >📄 القوالب</button>
        <button
          class="mode-btn"
          :class="{ active: mode === 'campaigns' }"
          @click="mode = 'campaigns'"
        >📣 الحملات</button>
      </div>
    </div>

    <!-- ============ CAMPAIGNS ============ -->
    <div v-if="mode === 'campaigns'" class="cmp-view">
      <div class="cmp-head">
        <h2 class="cmp-title">📣 حملات الواتساب</h2>
        <div class="cmp-actions">
          <span class="cmp-updated">تحديث يدوي — آخر تحديث: {{ lastUpdate }}</span>
          <button class="btn-dark" @click="loadCampaigns" :disabled="loading">
            {{ loading ? '...' : '↻ تحديث' }}
          </button>
          <button class="btn-success" @click="newCampaign">+ إنشاء حملة</button>
        </div>
      </div>

      <!-- Summary -->
      <div v-if="campaignsData" class="cmp-summary-card">
        <div class="summary-label">ملخص الأداء — كل الوقت</div>
        <div class="summary-grid">
          <div class="summary-cell red">
            <div class="sv">{{ campaignsData.summary.failed_pct }}%</div>
            <div class="sl">نسبة الفشل</div>
            <div class="sm">{{ campaignsData.summary.failed }} من {{ campaignsData.summary.targets }} مستهدف</div>
          </div>
          <div class="summary-cell blue">
            <div class="sv">{{ campaignsData.summary.read_pct }}%</div>
            <div class="sl">نسبة القراءة</div>
            <div class="sm">{{ campaignsData.summary.read }} من {{ campaignsData.summary.targets }} مستهدف</div>
          </div>
          <div class="summary-cell green">
            <div class="sv">{{ campaignsData.summary.delivered_pct }}%</div>
            <div class="sl">نسبة التسليم</div>
            <div class="sm">{{ campaignsData.summary.delivered }} من {{ campaignsData.summary.targets }} مستهدف</div>
          </div>
          <div class="summary-cell neutral">
            <div class="sv">{{ campaignsData.summary.campaigns_count }}</div>
            <div class="sl">الحملات</div>
            <div class="sm">{{ campaignsData.summary.completed_count }} مكتملة</div>
          </div>
        </div>
      </div>

      <!-- Status filters -->
      <div v-if="campaignsData" class="cmp-chips">
        <button
          v-for="f in campaignFilters" :key="f.id"
          class="chip"
          :class="{ active: campaignFilter === f.id }"
          @click="setCampaignFilter(f.id)"
        >{{ f.label }} ({{ campaignsData.status_counts[f.id] || 0 }})</button>
      </div>

      <!-- Cards -->
      <div class="cmp-list">
        <div v-for="c in filteredCampaigns" :key="c.name" class="cmp-card">
          <div class="card-head">
            <div>
              <div class="card-title">
                <span class="dot" :class="statusClass(c.status)"></span>
                {{ c.title || c.name }}
                <span class="badge" :class="statusClass(c.status)">{{ statusLabel(c.status) }}</span>
              </div>
              <div class="card-sub">القالب: {{ c.template || '—' }}</div>
            </div>
            <div class="card-actions">
              <button class="pill-btn dark" @click="openCampaign(c.name)">⚑ تفاصيل إضافية</button>
              <button class="pill-btn" @click="openCampaign(c.name)">📊 التقرير</button>
              <button class="pill-btn" @click="cloneCampaign(c.name)">📋 نسخ</button>
            </div>
          </div>

          <div class="metrics">
            <div class="metric red" @click="openCampaign(c.name)"><div class="mv">{{ c.failed }}</div><div class="ml">فشل ▾</div></div>
            <div class="metric blue" @click="openCampaign(c.name)"><div class="mv">{{ c.read }}</div><div class="ml">قُرئ ▾</div></div>
            <div class="metric green" @click="openCampaign(c.name)"><div class="mv">{{ c.delivered }}</div><div class="ml">وصل ▾</div></div>
            <div class="metric neutral" @click="openCampaign(c.name)"><div class="mv">{{ c.targets }}</div><div class="ml">المستهدفون ▾</div></div>
          </div>

          <div class="card-hint">↙ اضغط على أي رقم لعرض قائمة المستلمين</div>

          <div class="progress-bar" :title="'وصل ' + pct(c.delivered, c.targets) + '% — قُرئ ' + pct(c.read, c.targets) + '% — فشل ' + pct(c.failed, c.targets) + '%'">
            <span class="seg green" :style="{ width: pct(c.delivered, c.targets) + '%' }"></span>
            <span class="seg blue" :style="{ width: pct(c.read, c.targets) + '%' }"></span>
            <span class="seg red" :style="{ width: pct(c.failed, c.targets) + '%' }"></span>
          </div>
          <div class="progress-legend">
            <span class="g">{{ pct(c.delivered, c.targets) }}% وصل</span>
            <span class="b">{{ pct(c.read, c.targets) }}% قُرئ</span>
            <span class="r">{{ pct(c.failed, c.targets) }}% فشل</span>
          </div>
        </div>

        <div v-if="!loading && !filteredCampaigns.length" class="empty">
          لا توجد حملات تطابق الفلتر الحالي.
        </div>
      </div>
    </div>

    <!-- ============ TEMPLATES ============ -->
    <div v-else class="cmp-view">
      <div class="cmp-head">
        <h2 class="cmp-title">📄 إدارة القوالب</h2>
        <div class="cmp-actions">
          <button class="btn-dark" @click="loadTemplates" :disabled="loadingT">
            {{ loadingT ? '...' : '↻ تحديث' }}
          </button>
          <button class="btn-success" @click="newTemplate">+ إنشاء قالب</button>
        </div>
      </div>

      <div class="cmp-chips">
        <button
          v-for="f in templateFilters" :key="f.id"
          class="chip"
          :class="{ active: templateFilter === f.id }"
          @click="setTemplateFilter(f.id)"
        >{{ f.label }} ({{ templatesData?.status_counts?.[f.id] || 0 }})</button>
      </div>

      <div class="tpl-filters">
        <input type="text" v-model="templateSearch" @input="debouncedLoad" placeholder="ابحث بالاسم أو النص..." class="tpl-search" />
        <select v-model="templateType"><option value="">كل الأنواع</option><option>MARKETING</option><option>UTILITY</option><option>AUTHENTICATION</option></select>
        <select v-model="templateSort"><option value="name">الاسم</option><option value="modified">آخر تعديل</option></select>
      </div>

      <div class="tpl-meta">متوسط وقت الاعتماد: 24 ساعة. المُعلَّق المتجاوز للمتوسط: 0</div>

      <div class="tpl-list">
        <div v-for="t in filteredTemplates" :key="t.name" class="tpl-card">
          <div class="tpl-card-left">
            <div class="tpl-name">
              <span v-if="(t.status||'').toLowerCase() === 'approved'" class="ok-dot">✓</span>
              {{ t.template_name || t.name }}
              <span class="tpl-sub">{{ t.actual_name || t.name }} ({{ t.language_code || 'en' }})</span>
            </div>
          </div>
          <div class="tpl-card-right">
            <span class="tpl-status" :class="statusClass(t.status)">{{ statusLabel(t.status) }}</span>
            <button class="pill-btn" @click="previewTemplate(t)">👁 عرض</button>
            <button class="pill-btn" @click="cloneTemplate(t)">📋 نسخ</button>
          </div>
        </div>
        <div v-if="!loadingT && !filteredTemplates.length" class="empty">لا توجد قوالب.</div>
      </div>
    </div>

    <!-- Modals -->
    <CampaignDetailModal
      v-if="activeCampaign"
      :campaign-name="activeCampaign"
      @close="activeCampaign = null"
    />
    <TemplatePreviewModal
      v-if="activeTemplate"
      :template="activeTemplate"
      @close="activeTemplate = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useFrappe } from '@/composables/useFrappe';
import CampaignDetailModal from './CampaignDetailModal.vue';
import TemplatePreviewModal from './TemplatePreviewModal.vue';

const { call } = useFrappe();

const mode = ref('campaigns');
const campaignsData = ref(null);
const templatesData = ref(null);
const loading = ref(false);
const loadingT = ref(false);
const activeCampaign = ref(null);
const activeTemplate = ref(null);
const lastUpdate = ref('');

const campaignFilter = ref('all');
const templateFilter = ref('all');
const templateSearch = ref('');
const templateType = ref('');
const templateSort = ref('modified');

const campaignFilters = [
  { id: 'all', label: 'الكل' },
  { id: 'ongoing', label: 'جارية' },
  { id: 'completed', label: 'مكتملة' },
  { id: 'scheduled', label: 'مجدولة' },
  { id: 'draft', label: 'مسودة' },
  { id: 'cancelled', label: 'ملغاة' },
];
const templateFilters = [
  { id: 'all', label: 'الكل' },
  { id: 'approved', label: 'معتمد' },
  { id: 'pending', label: 'قيد المراجعة' },
  { id: 'rejected', label: 'مرفوض' },
];

const filteredCampaigns = computed(() => {
  const cs = campaignsData.value?.campaigns || [];
  if (campaignFilter.value === 'all') return cs;
  return cs.filter(c => matchesFilter(c.status, campaignFilter.value));
});

function matchesFilter(status, filter) {
  const s = (status || '').toLowerCase();
  if (filter === 'ongoing') return s === 'in progress' || s === 'queued';
  if (filter === 'completed') return s === 'completed';
  if (filter === 'scheduled') return s === 'queued';
  if (filter === 'draft') return s === 'draft';
  if (filter === 'cancelled') return s === 'cancelled' || s === 'partially failed';
  return true;
}

const filteredTemplates = computed(() => {
  let ts = templatesData.value?.templates || [];
  if (templateType.value) ts = ts.filter(t => (t.category || '').toUpperCase() === templateType.value);
  if (templateSort.value === 'name') ts = [...ts].sort((a, b) => (a.template_name || '').localeCompare(b.template_name || ''));
  return ts;
});

function statusClass(s) {
  const x = (s || '').toLowerCase();
  if (x === 'completed' || x === 'approved' || x === 'success' || x === 'sent' || x === 'delivered') return 'ok';
  if (x === 'in progress' || x === 'queued' || x === 'pending' || x === 'in review') return 'progress';
  if (x === 'draft') return 'draft';
  if (x === 'cancelled' || x === 'rejected' || x === 'failed' || x === 'partially failed') return 'danger';
  return 'neutral';
}
function statusLabel(s) {
  const map = {
    'Completed': 'مكتملة', 'In Progress': 'جارية', 'Queued': 'مجدولة',
    'Draft': 'مسودة', 'Cancelled': 'ملغاة', 'Partially Failed': 'فشل جزئي',
    'Approved': 'معتمد', 'Pending': 'قيد المراجعة', 'In Review': 'قيد المراجعة',
    'Rejected': 'مرفوض',
  };
  return map[s] || s || '—';
}

function pct(n, d) { return d ? Math.round((n / d) * 100) : 0; }

async function loadCampaigns() {
  loading.value = true;
  try {
    campaignsData.value = await call('get_campaigns');
    lastUpdate.value = new Date().toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
  } finally { loading.value = false; }
}

async function loadTemplates() {
  loadingT.value = true;
  try {
    templatesData.value = await call('get_templates', {
      status: templateFilter.value,
      search: templateSearch.value,
    });
  } finally { loadingT.value = false; }
}

function setCampaignFilter(id) {
  campaignFilter.value = id;
}
function setTemplateFilter(id) {
  templateFilter.value = id;
  loadTemplates();
}

let debounceTimer = null;
function debouncedLoad() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadTemplates, 300);
}

function openCampaign(name) { activeCampaign.value = name; }
function previewTemplate(t) { activeTemplate.value = t; }

function newCampaign() { window.open('/app/bulk-whatsapp-message/new', '_blank'); }
function newTemplate() { window.open('/app/whatsapp-templates/new', '_blank'); }
function cloneCampaign(name) { window.open('/app/bulk-whatsapp-message/' + encodeURIComponent(name), '_blank'); }
function cloneTemplate(t) { window.open('/app/whatsapp-templates/' + encodeURIComponent(t.name), '_blank'); }

onMounted(() => {
  loadCampaigns();
  loadTemplates();
});
</script>

<style scoped>
.cmp-root {
  padding: 20px;
  overflow-y: auto;
  height: 100%;
  background: #f5f7f8;
}
.cmp-mode-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}
.cmp-mode-toggle {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 24px;
  padding: 3px;
  display: inline-flex;
  gap: 2px;
}
.mode-btn {
  border: none;
  background: transparent;
  padding: 7px 16px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  color: #3b4a54;
  font-weight: 500;
}
.mode-btn.active { background: #f59e0b; color: #fff; }

.cmp-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 10px;
}
.cmp-title { font-size: 18px; margin: 0; color: #111b21; font-weight: 700; }
.cmp-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.cmp-updated { color: #98a2a7; font-size: 12px; }

.btn-dark, .btn-success, .pill-btn {
  border: 1px solid transparent;
  border-radius: 20px;
  padding: 7px 14px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
}
.btn-dark { background: #1a1f22; color: #fff; }
.btn-dark:hover { background: #2d3336; }
.btn-success { background: #10b981; color: #fff; }
.btn-success:hover { background: #0ba472; }
.pill-btn { background: #fff; color: #3b4a54; border-color: #e0e5e7; }
.pill-btn:hover { background: #f3f5f6; }
.pill-btn.dark { background: #1a1f22; color: #fff; border-color: #1a1f22; }

.cmp-summary-card {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}
.summary-label { font-size: 12px; color: #667781; margin-bottom: 10px; text-align: left; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
@media (max-width: 780px) { .summary-grid { grid-template-columns: 1fr 1fr; } }
.summary-cell {
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
}
.summary-cell.red { background: #fef2f3; }
.summary-cell.blue { background: #eaf2fb; }
.summary-cell.green { background: #ecf7ee; }
.summary-cell.neutral { background: #f8fafb; }
.summary-cell .sv { font-size: 24px; font-weight: 700; }
.summary-cell.red .sv { color: #c0392b; }
.summary-cell.blue .sv { color: #2563eb; }
.summary-cell.green .sv { color: #10b981; }
.summary-cell.neutral .sv { color: #111b21; }
.summary-cell .sl { font-size: 11px; color: #3b4a54; margin-top: 4px; }
.summary-cell .sm { font-size: 10px; color: #667781; margin-top: 2px; }

.cmp-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 14px;
  justify-content: flex-end;
}
.chip {
  border: 1px solid #e0e5e7;
  background: #fff;
  border-radius: 18px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  color: #3b4a54;
}
.chip:hover { background: #f3f5f6; }
.chip.active { background: #f59e0b; color: #fff; border-color: #f59e0b; }

.cmp-list { display: flex; flex-direction: column; gap: 14px; }
.cmp-card {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 16px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.card-title {
  font-size: 15px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-sub { font-size: 12px; color: #667781; margin-top: 2px; }
.card-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.ok { background: #10b981; }
.dot.progress { background: #f59e0b; }
.dot.danger { background: #dc2626; }
.dot.draft, .dot.neutral { background: #94a3b8; }

.badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}
.badge.ok { background: #d1fae5; color: #065f46; }
.badge.progress { background: #fef3c7; color: #92400e; }
.badge.danger { background: #fee2e2; color: #991b1b; }
.badge.draft, .badge.neutral { background: #f1f5f9; color: #475569; }

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}
@media (max-width: 780px) { .metrics { grid-template-columns: 1fr 1fr; } }
.metric {
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.1s;
}
.metric:hover { transform: translateY(-1px); }
.metric.red { background: #fef2f3; }
.metric.blue { background: #eaf2fb; }
.metric.green { background: #ecf7ee; }
.metric.neutral { background: #f8fafb; }
.metric .mv { font-size: 22px; font-weight: 700; }
.metric.red .mv { color: #c0392b; }
.metric.blue .mv { color: #2563eb; }
.metric.green .mv { color: #10b981; }
.metric.neutral .mv { color: #111b21; }
.metric .ml { font-size: 11px; color: #667781; margin-top: 2px; }

.card-hint { font-size: 11px; color: #667781; text-align: center; margin-bottom: 8px; }

.progress-bar {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: #e5e7eb;
}
.progress-bar .seg.green { background: #10b981; }
.progress-bar .seg.blue { background: #2563eb; }
.progress-bar .seg.red { background: #dc2626; }
.progress-legend {
  display: flex; justify-content: space-between;
  font-size: 11px; margin-top: 5px; font-weight: 600;
}
.progress-legend .g { color: #10b981; }
.progress-legend .b { color: #2563eb; }
.progress-legend .r { color: #dc2626; }

.tpl-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  justify-content: flex-end;
}
.tpl-filters input, .tpl-filters select {
  padding: 7px 12px;
  border: 1px solid #e0e5e7;
  border-radius: 18px;
  font-size: 12px;
  background: #fff;
}
.tpl-search { min-width: 200px; }

.tpl-meta {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 12px;
  color: #667781;
  margin-bottom: 12px;
}

.tpl-list { display: flex; flex-direction: column; gap: 10px; }
.tpl-card {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.tpl-name { font-size: 14px; font-weight: 700; display: flex; align-items: center; gap: 6px; }
.tpl-sub { font-size: 11px; color: #667781; font-weight: 400; }
.ok-dot { color: #10b981; font-size: 14px; }
.tpl-card-right { display: flex; gap: 6px; align-items: center; }
.tpl-status { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.tpl-status.ok { background: #d1fae5; color: #065f46; }
.tpl-status.progress { background: #fef3c7; color: #92400e; }
.tpl-status.danger { background: #fee2e2; color: #991b1b; }

.empty {
  padding: 40px;
  text-align: center;
  color: #98a2a7;
  font-size: 13px;
  background: #fff;
  border-radius: 8px;
}
</style>
