<template>
  <div class="conv-list-panel">
    <!-- Header -->
    <div class="conv-panel-header">
      <div class="conv-header-title">
        <span class="wa-logo">💬</span>
        <span>محادثات الواتساب</span>
        <span class="live-dot"></span>
        <span class="live-text">مباشر</span>
      </div>
      <button class="conv-refresh-btn" @click="store.fetchConversations(true)" title="تحديث">🔄</button>
    </div>

    <!-- Search -->
    <div class="conv-search">
      <input
        type="text"
        v-model="store.search"
        @input="onSearch"
        placeholder="بحث... (/)"
        class="conv-search-input"
      />
    </div>

    <!-- Filters -->
    <div class="conv-filters">
      <button
        v-for="f in filters"
        :key="f.value"
        class="conv-filter-btn"
        :class="{ active: store.filter === f.value }"
        @click="setFilter(f.value)"
      >
        {{ f.label }}
        <span v-if="f.count > 0" class="filter-badge">{{ f.count }}</span>
      </button>
    </div>

    <!-- Sort bar -->
    <div class="conv-sort-bar">
      <span class="conv-sort-label">العرض: <strong>قائمة</strong></span>
      <span class="conv-sort-order">الأحدث ⌄</span>
    </div>

    <!-- List -->
    <div class="conv-list" ref="listRef" @scroll="onScroll">
      <div v-if="store.loading && store.conversations.length === 0" class="conv-loading">
        <div class="loading-spinner"></div>
        جاري التحميل...
      </div>
      <ConversationItem
        v-for="c in store.conversations"
        :key="c.name"
        :conv="c"
        :is-selected="store.selected?.name === c.name"
        @select="selectConv"
      />
      <div v-if="store.loading && store.conversations.length > 0" class="conv-loading-more">
        <div class="loading-spinner small"></div>
      </div>
      <div v-if="!store.loading && store.conversations.length === 0" class="conv-empty">
        <span class="conv-empty-icon">📭</span>
        <span>لا توجد محادثات</span>
      </div>
    </div>

    <!-- Count -->
    <div class="conv-count">
      <span>{{ store.total }} محادثة</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useConversationsStore } from '@/stores/conversations';
import ConversationItem from './ConversationItem.vue';

const store = useConversationsStore();
const listRef = ref(null);
let searchTimeout = null;

const filters = computed(() => [
  { label: 'الكل', value: 'all', count: 0 },
  { label: 'غير مقروء', value: 'unread', count: 0 },
  { label: 'لي', value: 'mine', count: 0 },
  { label: 'متأخرة', value: 'escalated', count: 0 },
]);

function setFilter(f) {
  store.filter = f;
  store.fetchConversations(true);
}

function onSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    store.fetchConversations(true);
  }, 300);
}

function selectConv(conv) {
  store.selectConversation(conv);
}

function onScroll() {
  const el = listRef.value;
  if (!el) return;
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
    store.loadMore();
  }
}

onMounted(() => {
  store.fetchConversations(true);
});
</script>
