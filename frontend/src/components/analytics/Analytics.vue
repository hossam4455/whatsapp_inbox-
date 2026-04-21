<template>
  <div class="analytics-root">
    <div class="analytics-header">
      <h2 class="analytics-title">تحليلات الواتساب</h2>
      <div class="analytics-actions">
        <button class="a-tab" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">نظرة عامة</button>
        <button class="a-tab" :class="{ active: tab === 'campaigns' }" @click="tab = 'campaigns'">الحملات</button>
        <button class="a-tab" :class="{ active: tab === 'team' }" @click="tab = 'team'">أداء الفريق</button>
        <button class="a-refresh" @click="load" :disabled="loading">
          {{ loading ? '...' : '↻ تحديث' }}
        </button>
      </div>
    </div>

    <!-- Status banner -->
    <div v-if="data" class="analytics-status" :class="data.avg_response.status_class">
      <span>حالة سرعة الرد: </span>
      <strong>{{ data.avg_response.status }}</strong>
    </div>

    <div v-if="loading && !data" class="analytics-loading">جاري التحميل...</div>

    <!-- Overview -->
    <div v-if="data && tab === 'overview'" class="analytics-grid">
      <!-- Most requested property type -->
      <div class="a-card soft-pink">
        <div class="a-card-head">
          <span class="a-card-label">النوع الأكثر طلباً</span>
          <span class="a-card-icon">🏠</span>
        </div>
        <div class="a-card-value">{{ data.top_property_type || 'لا توجد بيانات' }}</div>
        <div class="a-card-hint">نوع العقار الأكثر طلباً في المحادثات</div>
      </div>

      <!-- Avg response time -->
      <div class="a-card soft-blue">
        <div class="a-card-head">
          <span class="a-card-label">متوسط وقت الرد</span>
          <span class="a-card-icon">⏱</span>
        </div>
        <div class="a-card-value">
          <template v-if="data.avg_response.minutes">
            {{ data.avg_response.hours }} ساعة {{ data.avg_response.rem_minutes }} د
          </template>
          <template v-else>—</template>
        </div>
        <div class="a-card-hint">الوقت المتوسط للرد على رسائل العملاء</div>
      </div>

      <!-- Waiting count -->
      <div class="a-card soft-yellow">
        <div class="a-card-head">
          <span class="a-card-label">في انتظار الرد</span>
          <span class="a-card-icon">👥</span>
        </div>
        <div class="a-card-value">{{ data.waiting_count }}</div>
        <div class="a-card-hint">محادثات تحتاج متابعة</div>
      </div>

      <!-- Top agents -->
      <div class="a-card wide soft-cream">
        <div class="a-card-head">
          <span class="a-card-label">أفضل 3 موظفين (ردوداً)</span>
          <span class="a-card-icon">🏆</span>
        </div>
        <div class="a-card-sub">آخر {{ data.period_days }} يوم</div>
        <ul class="a-agent-list">
          <li v-for="(a, i) in data.top_agents.slice(0, 3)" :key="a.owner">
            <span class="a-agent-medal" :class="'m-' + i">{{ ['🥇','🥈','🥉'][i] }}</span>
            <span class="a-agent-name">{{ a.name }}</span>
            <span class="a-agent-meta">{{ a.messages }} رسالة · {{ a.conversations }} محادثة</span>
            <span class="a-agent-score">{{ a.messages }}</span>
          </li>
          <li v-if="!data.top_agents.length" class="a-empty">لا توجد بيانات</li>
        </ul>
      </div>

      <!-- Totals -->
      <div class="a-card soft-green">
        <div class="a-card-head">
          <span class="a-card-label">إجمالي الرسائل</span>
          <span class="a-card-icon">💬</span>
        </div>
        <div class="a-card-value">{{ data.totals.messages.toLocaleString('ar') }}</div>
        <div class="a-card-hint">آخر {{ data.period_days }} يوم</div>
      </div>

      <!-- Conversations -->
      <div class="a-card soft-purple">
        <div class="a-card-head">
          <span class="a-card-label">المحادثات المفتوحة</span>
          <span class="a-card-icon">📂</span>
        </div>
        <div class="a-card-value">{{ data.totals.open_conversations }}</div>
        <div class="a-card-hint">من أصل {{ data.totals.conversations }} محادثة</div>
      </div>

      <!-- SLA -->
      <div class="a-card wide">
        <div class="a-card-head">
          <span class="a-card-label">مستوى الخدمة (SLA)</span>
          <span class="a-card-icon">⚠️</span>
        </div>
        <div class="a-card-sub">محادثات تجاوزت وقت الرد المحدد</div>
        <div class="a-sla">
          <div class="a-sla-cell">
            <div class="a-sla-label">حرج (+60 د)</div>
            <div class="a-sla-value danger">{{ data.sla.critical }}</div>
          </div>
          <div class="a-sla-cell">
            <div class="a-sla-label">تحذير (+10 د)</div>
            <div class="a-sla-value warn">{{ data.sla.warning }}</div>
          </div>
        </div>

        <div class="a-team-header">توزيع على الفريق</div>
        <ul class="a-team-list">
          <li v-for="t in data.team_distribution" :key="t.name">
            <span>{{ t.name }}</span>
            <strong>{{ t.awaiting }} بانتظار</strong>
          </li>
          <li v-if="!data.team_distribution.length" class="a-empty">لا توجد بيانات</li>
        </ul>
      </div>
    </div>

    <!-- Team tab: fuller leaderboard -->
    <div v-if="data && tab === 'team'" class="analytics-grid">
      <div class="a-card wide">
        <div class="a-card-head">
          <span class="a-card-label">لوحة أداء الفريق</span>
          <span class="a-card-icon">🏅</span>
        </div>
        <table class="a-table">
          <thead>
            <tr><th>#</th><th>الموظف</th><th>الرسائل</th><th>المحادثات</th></tr>
          </thead>
          <tbody>
            <tr v-for="(a, i) in data.top_agents" :key="a.owner">
              <td>{{ i + 1 }}</td>
              <td>{{ a.name }}</td>
              <td>{{ a.messages }}</td>
              <td>{{ a.conversations }}</td>
            </tr>
            <tr v-if="!data.top_agents.length"><td colspan="4" class="a-empty">لا توجد بيانات</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Campaigns placeholder -->
    <div v-if="data && tab === 'campaigns'" class="analytics-grid">
      <div class="a-card wide">
        <div class="a-card-head">
          <span class="a-card-label">الحملات</span>
          <span class="a-card-icon">📣</span>
        </div>
        <div class="a-empty">لا توجد حملات — ابنِ قالب رسالة جماعية لتفعيل التحليل</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useFrappe } from '@/composables/useFrappe';

const { call } = useFrappe();
const tab = ref('overview');
const data = ref(null);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const res = await call('get_analytics', { period_days: 30 });
    data.value = res;
  } catch (e) {
    console.error('analytics load failed', e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.analytics-root {
  padding: 20px;
  overflow-y: auto;
  height: 100%;
  background: #fff;
}

.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.analytics-title { font-size: 20px; font-weight: 700; color: #111b21; margin: 0; }
.analytics-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.a-tab {
  border: 1px solid #e0e5e7;
  background: #fff;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  color: #3b4a54;
}
.a-tab:hover { background: #f3f5f6; }
.a-tab.active { background: #1a1f22; color: #fff; border-color: #1a1f22; }
.a-refresh {
  border: 1px solid #e0e5e7;
  background: #fff;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  color: #3b4a54;
}
.a-refresh:hover { background: #f3f5f6; }
.a-refresh:disabled { opacity: 0.5; cursor: wait; }

.analytics-status {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  margin-bottom: 16px;
}
.analytics-status.good { background: #e6f7ef; color: #067a46; }
.analytics-status.ok { background: #eaf2fb; color: #0d4d8a; }
.analytics-status.warn { background: #fde8ea; color: #a41724; }
.analytics-status.danger { background: #fde8ea; color: #a41724; }
.analytics-status.neutral { background: #f3f5f6; color: #3b4a54; }

.analytics-loading { padding: 40px; text-align: center; color: #667781; }

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.a-card {
  background: #fff;
  border: 1px solid #eef1f3;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.a-card.wide { grid-column: span 2; }
@media (max-width: 700px) {
  .a-card.wide { grid-column: span 1; }
}

.a-card.soft-pink { background: linear-gradient(135deg, #fff, #fff5f7); }
.a-card.soft-blue { background: linear-gradient(135deg, #fff, #f3f9ff); }
.a-card.soft-yellow { background: linear-gradient(135deg, #fff, #fffaf0); }
.a-card.soft-cream { background: linear-gradient(135deg, #fff, #fff9ef); }
.a-card.soft-green { background: linear-gradient(135deg, #fff, #f0faf5); }
.a-card.soft-purple { background: linear-gradient(135deg, #fff, #f6f4fe); }

.a-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.a-card-label { font-size: 13px; color: #667781; }
.a-card-icon {
  width: 34px; height: 34px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  background: #f3f5f6;
}
.a-card-value {
  font-size: 26px;
  font-weight: 700;
  color: #111b21;
  margin-top: 4px;
}
.a-card-hint { font-size: 12px; color: #0088cc; margin-top: 2px; }
.a-card-sub { font-size: 12px; color: #667781; margin-bottom: 6px; }

.a-agent-list {
  list-style: none; padding: 0; margin: 8px 0 0;
  display: flex; flex-direction: column; gap: 10px;
}
.a-agent-list li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  grid-template-rows: auto auto;
  grid-column-gap: 10px;
  align-items: center;
}
.a-agent-medal {
  grid-row: span 2;
  font-size: 20px;
}
.a-agent-name { font-weight: 600; color: #111b21; font-size: 14px; }
.a-agent-meta { font-size: 11px; color: #667781; }
.a-agent-score {
  grid-row: span 2;
  font-size: 16px;
  font-weight: 700;
  color: #d97706;
}

.a-sla {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  margin-top: 10px; margin-bottom: 14px;
}
.a-sla-cell {
  background: #fff; border: 1px solid #eef1f3; border-radius: 8px;
  padding: 12px; text-align: center;
}
.a-sla-label { font-size: 12px; color: #667781; margin-bottom: 4px; }
.a-sla-value { font-size: 22px; font-weight: 700; }
.a-sla-value.danger { color: #c0392b; }
.a-sla-value.warn { color: #d97706; }

.a-team-header {
  font-size: 13px; font-weight: 600; color: #3b4a54;
  margin-bottom: 6px; padding-top: 6px;
  border-top: 1px solid #eef1f3;
}
.a-team-list {
  list-style: none; padding: 0; margin: 0;
}
.a-team-list li {
  display: flex; justify-content: space-between;
  padding: 6px 0; font-size: 13px;
  border-bottom: 1px solid #f3f5f6;
}
.a-team-list li:last-child { border-bottom: none; }

.a-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}
.a-table th, .a-table td {
  padding: 10px 8px;
  text-align: right;
  border-bottom: 1px solid #eef1f3;
  font-size: 13px;
}
.a-table th { color: #667781; font-weight: 600; background: #f8fafb; }

.a-empty { padding: 20px; text-align: center; color: #98a2a7; font-size: 13px; }
</style>
