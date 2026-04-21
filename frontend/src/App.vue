<template>
  <div class="wa-inbox" dir="rtl">
    <!-- Top tab bar -->
    <div class="wa-top-tabs">
      <button
        v-for="t in tabs" :key="t.id"
        class="wa-top-tab"
        :class="{ active: view === t.id }"
        @click="view = t.id"
      >
        <span>{{ t.icon }}</span> {{ t.label }}
      </button>
    </div>

    <!-- Conversations view -->
    <div v-if="view === 'chats'" class="wa-inbox-layout">
      <ConversationList class="wa-panel-conversations" />
      <ChatWindow class="wa-panel-chat" />
      <ConversationDashboard
        v-if="showDashboard"
        class="wa-panel-dashboard"
        @hide="showDashboard = false"
      />
      <button
        v-else
        class="wa-dashboard-show"
        @click="showDashboard = true"
        title="إظهار اللوحة"
      >◀ إظهار اللوحة</button>
    </div>

    <!-- Analytics view -->
    <Analytics v-else-if="view === 'analytics'" class="wa-view-full" />

    <!-- Campaigns view -->
    <Campaigns v-else-if="view === 'campaigns'" class="wa-view-full" />

    <!-- Settings view -->
    <Settings v-else-if="view === 'settings'" class="wa-view-full" />

    <div v-else class="wa-view-placeholder">
      <span>{{ tabs.find(t => t.id === view)?.label }} — قيد التطوير</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ConversationList from '@/components/conversations/ConversationList.vue';
import ChatWindow from '@/components/chat/ChatWindow.vue';
import ConversationDashboard from '@/components/chat/ConversationDashboard.vue';
import Analytics from '@/components/analytics/Analytics.vue';
import Settings from '@/components/settings/Settings.vue';
import Campaigns from '@/components/campaigns/Campaigns.vue';

const showDashboard = ref(true);
const view = ref('chats');

const tabs = [
  { id: 'chats', label: 'المحادثات', icon: '💬' },
  { id: 'campaigns', label: 'الحملات', icon: '📣' },
  { id: 'tools', label: 'الأدوات', icon: '🛠' },
  { id: 'analytics', label: 'التحليلات', icon: '📊' },
  { id: 'supervision', label: 'الإشراف', icon: '👥' },
  { id: 'settings', label: 'الإعدادات', icon: '⚙️' },
];
</script>

<style>
/* ============================================================
   WhatsApp Inbox - Premium Style
   ============================================================ */

:root {
  --wa-green: #00a884;
  --wa-green-dark: #008069;
  --wa-green-light: #d9fdd3;
  --wa-teal: #075e54;
  --wa-teal-dark: #054640;
  --wa-bg: #efeae2;
  --wa-bg-pattern: #e5ddd5;
  --wa-sidebar-bg: #fff;
  --wa-header-bg: #f0f2f5;
  --wa-border: #e9edef;
  --wa-text: #111b21;
  --wa-text-secondary: #667781;
  --wa-bubble-out: #d9fdd3;
  --wa-bubble-in: #fff;
  --wa-unread: #25d366;
  --wa-danger: #ea0038;
  --wa-shadow: 0 1px 3px rgba(11,20,26,0.08);
}

* { box-sizing: border-box; }

.wa-inbox {
  height: calc(100vh - 80px);
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans Arabic', Tahoma, sans-serif;
  background: #d1d7db;
  display: flex;
  flex-direction: column;
}

.wa-top-tabs {
  display: flex;
  gap: 6px;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid var(--wa-border);
  overflow-x: auto;
  flex-wrap: wrap;
  justify-content: center;
}
.wa-top-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #e0e5e7;
  background: #fff;
  border-radius: 24px;
  padding: 8px 18px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: #3b4a54;
  white-space: nowrap;
  transition: all 0.15s;
}
.wa-top-tab:hover { background: #f3f5f6; }
.wa-top-tab.active {
  background: var(--wa-green);
  color: #fff;
  border-color: var(--wa-green);
}

.wa-inbox-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  box-shadow: 0 6px 18px rgba(11,20,26,0.15);
}

.wa-view-full {
  flex: 1;
  min-height: 0;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  overflow: auto;
  background: #fff;
}
.wa-view-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667781;
  font-size: 15px;
  background: #fff;
}

/* ============================================================
   DASHBOARD PANEL
   ============================================================ */
.wa-panel-dashboard {
  width: 280px;
  min-width: 240px;
  max-width: 320px;
  border-right: 1px solid var(--wa-border);
  background: #f5f7f8;
  overflow: hidden;
  flex-shrink: 0;
}
.wa-dashboard-show {
  position: absolute;
  top: 100px;
  left: 10px;
  background: #1a1f22;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 8px 14px;
  font-size: 12px;
  cursor: pointer;
  z-index: 10;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.wa-dashboard-show:hover { background: #2d3336; }

@media (max-width: 880px) {
  .wa-panel-dashboard { display: none; }
}

/* ============================================================
   CONVERSATIONS PANEL
   ============================================================ */
.wa-panel-conversations {
  width: 300px;
  min-width: 260px;
  max-width: 360px;
  border-left: 1px solid var(--wa-border);
  display: flex;
  flex-direction: column;
  background: var(--wa-sidebar-bg);
  flex-shrink: 0;
}

/* Panel Header */
.conv-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #fff;
  border-bottom: 1px solid var(--wa-border);
}
.conv-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: var(--wa-text);
}
.wa-logo { font-size: 22px; }
.live-dot {
  width: 8px; height: 8px;
  background: #25d366;
  border-radius: 50%;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.live-text { font-size: 12px; color: #25d366; font-weight: 600; }
.conv-refresh-btn {
  background: none; border: none; font-size: 18px;
  cursor: pointer; padding: 6px; border-radius: 50%;
  transition: background 0.2s;
}
.conv-refresh-btn:hover { background: #f0f2f5; }

/* Search */
.conv-search { padding: 8px 14px; background: #fff; }
.conv-search-input {
  width: 100%;
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 14px;
  outline: none;
  direction: rtl;
  background: #f0f2f5;
  color: var(--wa-text);
  transition: all 0.2s;
}
.conv-search-input:focus { background: #fff; box-shadow: 0 0 0 2px rgba(0,168,132,0.25); }
.conv-search-input::placeholder { color: #8696a0; }

/* Filters */
.conv-filters {
  display: flex;
  gap: 6px;
  padding: 10px 14px;
  flex-wrap: wrap;
  background: #fff;
}
.conv-filter-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 20px;
  background: #f0f2f5;
  font-size: 13px;
  cursor: pointer;
  color: var(--wa-text);
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.conv-filter-btn:hover { background: #e4e6e8; }
.conv-filter-btn.active {
  background: #1b1b1b;
  color: #fff;
}
.filter-badge {
  background: var(--wa-danger);
  color: #fff;
  border-radius: 10px;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 700;
}

/* Sort Bar */
.conv-sort-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid var(--wa-border);
  background: #fafafa;
  font-size: 12px;
  color: var(--wa-text-secondary);
}
.conv-sort-label strong { color: var(--wa-text); }
.conv-sort-order { cursor: pointer; color: var(--wa-green); font-weight: 500; }

/* Conversation List */
.conv-list {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #c5c6c8 transparent;
}
.conv-list::-webkit-scrollbar { width: 5px; }
.conv-list::-webkit-scrollbar-thumb { background: #c5c6c8; border-radius: 3px; }

/* Conversation Item */
.conv-item {
  display: flex;
  align-items: flex-start;
  padding: 14px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f2f5;
  gap: 12px;
  transition: all 0.15s;
}
.conv-item:hover { background: #f5f6f6; }
.conv-item.active { background: #f0f2f5; border-right: 3px solid var(--wa-green); }
.conv-item.unread { background: #fafafa; }

/* Avatar */
.conv-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}
.av-green { background: linear-gradient(135deg, #00a884, #25d366); }
.av-blue { background: linear-gradient(135deg, #42a5f5, #1e88e5); }
.av-orange { background: linear-gradient(135deg, #ffa726, #f57c00); }
.av-purple { background: linear-gradient(135deg, #ab47bc, #8e24aa); }
.av-teal { background: linear-gradient(135deg, #26a69a, #00897b); }
.av-pink { background: linear-gradient(135deg, #ec407a, #d81b60); }

/* Conv Body */
.conv-body { flex: 1; min-width: 0; }

.conv-row-1 {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}
.conv-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--wa-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.conv-time {
  font-size: 11px;
  color: var(--wa-text-secondary);
  flex-shrink: 0;
}
.conv-item.unread .conv-time { color: var(--wa-unread); font-weight: 700; }

.conv-row-2 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}
.conv-status-pill {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.pill-active { background: #e8f5e9; color: #2e7d32; }
.pill-pending { background: #fff3e0; color: #e65100; }
.pill-replied { background: #e3f2fd; color: #1565c0; }
.pill-escalated { background: #fce4ec; color: #c62828; }
.pill-closed { background: #f5f5f5; color: #757575; }
.conv-assigned-tag {
  font-size: 11px;
  color: var(--wa-text-secondary);
  background: #f0f2f5;
  padding: 2px 8px;
  border-radius: 10px;
}

.conv-row-3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.conv-preview-text {
  font-size: 13px;
  color: var(--wa-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  line-height: 1.3;
}
.conv-item.unread .conv-preview-text { color: var(--wa-text); font-weight: 500; }
.conv-badge {
  background: var(--wa-unread);
  color: #fff;
  border-radius: 50%;
  min-width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

/* Count footer */
.conv-count {
  padding: 10px 14px;
  font-size: 12px;
  color: var(--wa-text-secondary);
  border-top: 1px solid var(--wa-border);
  text-align: center;
  background: #fafafa;
  font-weight: 500;
}

/* Loading states */
.conv-loading, .conv-loading-more, .conv-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--wa-text-secondary);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.conv-empty-icon { font-size: 40px; opacity: 0.5; }
.loading-spinner {
  width: 30px; height: 30px;
  border: 3px solid #e9edef;
  border-top-color: var(--wa-green);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.loading-spinner.small { width: 20px; height: 20px; border-width: 2px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ============================================================
   CHAT PANEL
   ============================================================ */
.wa-panel-chat {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--wa-bg-pattern);
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 54c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm25-25c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM5 34c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z' fill='%23d4cfc4' fill-opacity='.3'/%3E%3C/svg%3E");
}

/* Chat Header */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--wa-header-bg);
  border-bottom: 1px solid var(--wa-border);
  min-height: 56px;
}
.chat-header-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chat-header-info strong {
  font-size: 15px;
  color: var(--wa-text);
}
.chat-header-phone {
  font-size: 12px;
  color: var(--wa-text-secondary);
  direction: ltr;
}
.chat-status-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 500;
}
.status-active { background: #e8f5e9; color: #2e7d32; }
.status-pending { background: #fff3e0; color: #e65100; }
.status-replied { background: #e3f2fd; color: #1565c0; }
.status-escalated { background: #fce4ec; color: #c62828; }
.status-closed { background: #f5f5f5; color: #757575; }

/* Messages Area */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 60px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  scrollbar-width: thin;
  scrollbar-color: rgba(0,0,0,0.15) transparent;
}
.chat-messages::-webkit-scrollbar { width: 6px; }
.chat-messages::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 3px; }

.chat-load-more {
  text-align: center;
  padding: 10px;
  margin-bottom: 10px;
}
.chat-load-more:hover { cursor: pointer; }
.chat-load-more span,
.chat-load-more {
  color: var(--wa-teal);
  font-size: 13px;
  background: rgba(255,255,255,0.85);
  padding: 6px 16px;
  border-radius: 18px;
  display: inline-block;
  box-shadow: var(--wa-shadow);
}
.chat-loading { text-align: center; padding: 60px; color: var(--wa-text-secondary); }

/* Message Bubbles */
.msg-row { display: flex; margin: 1px 0; }
.msg-row.incoming { justify-content: flex-end; }
.msg-row.outgoing { justify-content: flex-start; }

.msg-bubble {
  max-width: 55%;
  padding: 6px 9px 4px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.45;
  position: relative;
  word-wrap: break-word;
  box-shadow: 0 1px 0.5px rgba(11,20,26,0.13);
}
.msg-in {
  background: var(--wa-bubble-in);
  border-top-right-radius: 0;
}
.msg-out {
  background: var(--wa-bubble-out);
  border-top-left-radius: 0;
}

.msg-text { white-space: pre-wrap; color: var(--wa-text); }

.msg-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  margin-top: 1px;
}
.msg-time { font-size: 11px; color: #667781; }
.msg-status { font-size: 14px; color: #53bdeb; }

/* Media */
.msg-image {
  max-width: 280px;
  max-height: 300px;
  border-radius: 8px;
  cursor: pointer;
  display: block;
  margin: 2px 0;
}
.msg-audio-player {
  max-width: 280px;
  height: 36px;
}
.msg-doc {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0,0,0,0.04);
  border-radius: 6px;
  margin: 2px 0;
}
.msg-doc-link {
  color: var(--wa-teal);
  text-decoration: none;
  font-weight: 500;
  font-size: 13px;
}
.msg-doc-link:hover { text-decoration: underline; }
.msg-doc-no-link { color: var(--wa-text-secondary); font-size: 13px; }

/* ============================================================
   REPLY BOX
   ============================================================ */
.reply-file-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #e1f3e8;
  margin: 0 12px;
  border-radius: 10px 10px 0 0;
  border: 1px solid #c8e6c9;
  border-bottom: none;
}
.reply-file-thumb {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #c8e6c9;
}
.reply-file-name {
  font-size: 13px;
  color: var(--wa-text);
  flex: 1;
  font-weight: 500;
}
.reply-file-remove {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--wa-danger);
  padding: 4px 8px;
  border-radius: 50%;
  transition: background 0.2s;
}
.reply-file-remove:hover { background: rgba(234,0,56,0.1); }

.reply-box {
  background: var(--wa-header-bg);
  padding: 6px 12px 10px;
  border-top: 1px solid var(--wa-border);
}
.reply-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
/* Voice Recording */
.reply-recording {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: #fce4ec;
  margin: 0 12px;
  border-radius: 10px 10px 0 0;
  border: 1px solid #f8bbd0;
  border-bottom: none;
}
.recording-dot {
  width: 12px; height: 12px;
  background: #e53935;
  border-radius: 50%;
  animation: pulse-red 1s infinite;
}
@keyframes pulse-red {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}
.recording-text { font-size: 13px; color: #c62828; font-weight: 600; flex: 1; }
.recording-cancel {
  background: none; border: none; font-size: 18px;
  cursor: pointer; color: #c62828; padding: 4px 8px;
  border-radius: 50%;
}
.recording-cancel:hover { background: rgba(198,40,40,0.1); }

.reply-attach-btn, .reply-voice-btn {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.2s;
  color: #54656f;
}
.reply-attach-btn:hover, .reply-voice-btn:hover { background: #e9edef; }
.reply-voice-btn.recording {
  color: #e53935;
  animation: pulse-red 1s infinite;
}

.reply-input {
  flex: 1;
  border: 1px solid #e9edef;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  direction: auto;
  background: #fff;
  color: var(--wa-text);
  min-height: 42px;
  max-height: 120px;
  line-height: 1.4;
  transition: border-color 0.2s;
}
.reply-input:focus { border-color: var(--wa-green); }
.reply-input::placeholder { color: #8696a0; }

.reply-send-btn {
  padding: 0;
  width: 42px;
  height: 42px;
  background: var(--wa-green);
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, transform 0.1s;
  flex-shrink: 0;
}
.reply-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.reply-send-btn:hover:not(:disabled) {
  background: var(--wa-green-dark);
  transform: scale(1.05);
}
.reply-send-btn:active:not(:disabled) { transform: scale(0.95); }

/* ============================================================
   EMPTY STATE
   ============================================================ */
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: var(--wa-text-secondary);
  gap: 12px;
}
.chat-empty-icon { font-size: 72px; opacity: 0.4; }
.chat-empty p { font-size: 15px; color: #8696a0; }

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 900px) {
  .wa-panel-conversations { width: 280px; min-width: 240px; }
  .chat-messages { padding: 16px 20px; }
  .msg-bubble { max-width: 75%; }
}
</style>
