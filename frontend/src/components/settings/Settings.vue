<template>
  <div class="settings-root">
    <aside class="settings-side">
      <div class="side-label">الإعدادات</div>
      <button
        v-for="t in tabs" :key="t.id"
        class="side-tab"
        :class="{ active: tab === t.id }"
        @click="tab = t.id"
      >
        <span>{{ t.icon }}</span> {{ t.label }}
      </button>
    </aside>

    <main class="settings-main">
      <!-- Organization -->
      <div v-if="tab === 'org'" class="settings-card">
        <h3 class="settings-title">📅 إعدادات أوقات العمل</h3>
        <p class="settings-desc">
          تُستخدم هذه الإعدادات لاحقاً في احتساب أداء الفريق واستجابة الغياب التلقائية خارج أوقات العمل.
        </p>

        <div class="field">
          <label>أيام العمل</label>
          <div class="pills">
            <button
              v-for="d in days" :key="d.value"
              class="pill"
              :class="{ on: settings.work_days.includes(d.value) }"
              @click="toggleDay(d.value)"
              type="button"
            >{{ d.label }}</button>
          </div>
        </div>

        <div class="row-3">
          <div class="field">
            <label>بداية العمل</label>
            <input type="time" v-model="settings.start_time" />
          </div>
          <div class="field">
            <label>نهاية العمل</label>
            <input type="time" v-model="settings.end_time" />
          </div>
          <div class="field">
            <label>المنطقة الزمنية</label>
            <select v-model="settings.timezone">
              <option value="Asia/Riyadh">Asia/Riyadh (AST +3)</option>
              <option value="Asia/Dubai">Asia/Dubai (GST +4)</option>
              <option value="Africa/Cairo">Africa/Cairo (EET +2)</option>
              <option value="Asia/Kuwait">Asia/Kuwait (AST +3)</option>
              <option value="Asia/Qatar">Asia/Qatar (AST +3)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>

        <div class="field">
          <label>العطلات الرسمية</label>
          <div v-if="!settings.holidays.length" class="muted">لا توجد عطلات مضافة بعد.</div>
          <ul v-else class="holiday-list">
            <li v-for="(h, i) in settings.holidays" :key="i">
              <span>📅 {{ h.date }}</span>
              <span v-if="h.name" class="muted">— {{ h.name }}</span>
              <button class="x" @click="removeHoliday(i)">✕</button>
            </li>
          </ul>

          <div class="row-2">
            <div class="field">
              <label class="sub">التاريخ</label>
              <input type="date" v-model="newHoliday.date" />
            </div>
            <div class="field">
              <label class="sub">الاسم (اختياري)</label>
              <input type="text" v-model="newHoliday.name" placeholder="مثال: عيد الأضحى" />
            </div>
            <button class="btn-ghost small" @click="addHoliday" :disabled="!newHoliday.date">+ إضافة</button>
          </div>
        </div>

        <div class="notice">
          ملاحظة: هذه الإعدادات محفوظة ولكنها لا تؤثر حالياً على سلوك النظام. سيتم ربطها بمنطق الرد التلقائي في التحديث القادم.
        </div>

        <div class="actions">
          <button class="btn-ghost" @click="load" :disabled="loading">إعادة تحميل</button>
          <button class="btn-primary" @click="save" :disabled="saving">
            {{ saving ? 'جاري الحفظ...' : 'حفظ الإعدادات' }}
          </button>
        </div>
      </div>

      <!-- Teams placeholder -->
      <div v-else-if="tab === 'teams'" class="settings-card">
        <h3 class="settings-title">👥 إعدادات الفرق</h3>
        <p class="settings-desc">تعيين أعضاء الفرق والأدوار والتوزيع التلقائي — قيد التطوير.</p>
      </div>

      <!-- WhatsApp placeholder -->
      <div v-else-if="tab === 'whatsapp'" class="settings-card">
        <h3 class="settings-title">💬 إعدادات واتساب</h3>
        <p class="settings-desc">مفاتيح الـ API، أرقام الإرسال، القوالب — قيد التطوير.</p>
        <a class="btn-ghost small" href="/app/whatsapp-settings" target="_blank">فتح إعدادات Meta API →</a>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useFrappe } from '@/composables/useFrappe';

const { call } = useFrappe();

const tab = ref('org');
const tabs = [
  { id: 'org', label: 'المؤسسة', icon: '🏢' },
  { id: 'teams', label: 'الفرق', icon: '👥' },
  { id: 'whatsapp', label: 'واتساب', icon: '💬' },
];

// 0=Sunday (consistent with the screenshot that shows الأحد first and السبت last)
const days = [
  { value: 0, label: 'الأحد' },
  { value: 1, label: 'الاثنين' },
  { value: 2, label: 'الثلاثاء' },
  { value: 3, label: 'الأربعاء' },
  { value: 4, label: 'الخميس' },
  { value: 5, label: 'الجمعة' },
  { value: 6, label: 'السبت' },
];

const settings = ref({
  work_days: [0, 1, 2, 3, 4],
  start_time: '09:00',
  end_time: '18:00',
  timezone: 'Asia/Riyadh',
  holidays: [],
});
const newHoliday = ref({ date: '', name: '' });
const loading = ref(false);
const saving = ref(false);

async function load() {
  loading.value = true;
  try {
    const data = await call('get_inbox_settings');
    if (data) {
      settings.value = {
        work_days: Array.isArray(data.work_days) ? data.work_days : [0, 1, 2, 3, 4],
        start_time: data.start_time || '09:00',
        end_time: data.end_time || '18:00',
        timezone: data.timezone || 'Asia/Riyadh',
        holidays: Array.isArray(data.holidays) ? data.holidays : [],
      };
    }
  } finally { loading.value = false; }
}

async function save() {
  saving.value = true;
  try {
    await call('save_inbox_settings', { settings: JSON.stringify(settings.value) });
    alert('تم الحفظ');
  } catch {
    alert('فشل الحفظ');
  } finally { saving.value = false; }
}

function toggleDay(v) {
  const i = settings.value.work_days.indexOf(v);
  if (i === -1) settings.value.work_days.push(v);
  else settings.value.work_days.splice(i, 1);
}
function addHoliday() {
  if (!newHoliday.value.date) return;
  settings.value.holidays.push({ ...newHoliday.value });
  newHoliday.value = { date: '', name: '' };
}
function removeHoliday(i) {
  settings.value.holidays.splice(i, 1);
}

onMounted(load);
</script>

<style scoped>
.settings-root {
  display: flex;
  gap: 16px;
  padding: 20px;
  height: 100%;
  background: #f5f7f8;
  overflow: auto;
}

.settings-side {
  width: 220px;
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: fit-content;
}
.side-label { font-size: 12px; color: #98a2a7; padding: 4px 8px; margin-bottom: 4px; }
.side-tab {
  text-align: right;
  border: none;
  background: transparent;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #3b4a54;
  display: flex;
  align-items: center;
  gap: 8px;
}
.side-tab:hover { background: #f3f5f6; }
.side-tab.active { background: #fff3e0; color: #d97706; font-weight: 600; }

.settings-main { flex: 1; min-width: 0; }

.settings-card {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 10px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.settings-title { margin: 0; font-size: 17px; font-weight: 700; color: #111b21; }
.settings-desc { margin: 0; color: #667781; font-size: 13px; line-height: 1.6; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; color: #3b4a54; font-weight: 500; }
.field label.sub { color: #98a2a7; font-weight: 400; }

.field input, .field select {
  padding: 8px 10px;
  border: 1px solid #e0e5e7;
  border-radius: 6px;
  font-family: inherit;
  font-size: 13px;
  background: #fff;
}
.field input:focus, .field select:focus {
  outline: none;
  border-color: #00a884;
}

.pills { display: flex; flex-wrap: wrap; gap: 6px; }
.pill {
  border: 1px solid #e0e5e7;
  background: #fff;
  padding: 6px 14px;
  border-radius: 18px;
  cursor: pointer;
  font-size: 13px;
  color: #3b4a54;
  transition: all 0.15s;
}
.pill:hover { background: #f3f5f6; }
.pill.on {
  background: #d97706;
  color: #fff;
  border-color: #d97706;
}

.row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
  align-items: end;
}
@media (max-width: 700px) {
  .row-3, .row-2 { grid-template-columns: 1fr; }
}

.muted { color: #98a2a7; font-size: 13px; }

.holiday-list {
  list-style: none;
  padding: 0;
  margin: 0 0 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.holiday-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafb;
  border: 1px solid #eef1f3;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
}
.holiday-list .x {
  margin-inline-start: auto;
  background: none;
  border: none;
  color: #c0392b;
  cursor: pointer;
  font-size: 14px;
}

.notice {
  background: #eef6ff;
  border: 1px solid #c7ddf5;
  color: #1d4e89;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.btn-primary, .btn-ghost {
  padding: 9px 22px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid transparent;
  font-weight: 500;
}
.btn-primary { background: #00a884; color: #fff; }
.btn-primary:hover { background: #008f72; }
.btn-primary:disabled { opacity: 0.6; cursor: wait; }
.btn-ghost { background: #fff; color: #3b4a54; border-color: #e0e5e7; }
.btn-ghost:hover { background: #f3f5f6; }
.btn-ghost.small { padding: 6px 14px; font-size: 12px; text-decoration: none; display: inline-block; }
</style>
