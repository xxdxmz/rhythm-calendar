<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import zhCnLocale from '@fullcalendar/core/locales/zh-cn'
import type { CalendarOptions, EventClickArg } from '@fullcalendar/core'
import { Refresh, Calendar, Connection, TopRight } from '@element-plus/icons-vue'
import { useCalendarStore } from './stores/calendar'
import type { DynamicItem, EventItem } from './types'

const store = useCalendarStore()
const selected = ref<DynamicItem | null>(null)
const selectedEvent = ref<EventItem | null>(null)
const detailOpen = ref(false)

const statusText = computed(() => {
  if (!store.status?.last_success_at) return '等待首次同步'
  if (store.status.stale) return '缓存数据'
  return '同步正常'
})

const lastUpdated = computed(() => {
  if (!store.status?.last_success_at) return '尚未同步'
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(store.status.last_success_at))
})

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, timeGridPlugin],
  initialView: 'dayGridMonth',
  locale: zhCnLocale,
  firstDay: 1,
  height: 'auto',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek',
  },
  buttonText: { today: '今天', month: '月', week: '周' },
  events: store.calendarEvents,
  eventClick: openEvent,
  dayMaxEvents: 3,
  eventDisplay: 'block',
}))

function openEvent(arg: EventClickArg) {
  const sourceId = String(arg.event.extendedProps.source_dynamic_id || arg.event.id)
  selected.value = store.dynamics.find((item) => item.dynamic_id === sourceId) || null
  selectedEvent.value = store.events.find((item) => item.id === arg.event.id) || null
  detailOpen.value = true
}

function openDynamic(item: DynamicItem) {
  selected.value = item
  selectedEvent.value = null
  detailOpen.value = true
}

function eventTypeLabel(type: EventItem['event_type']) {
  return {
    VERSION_UPDATE: '版本更新', PACK_RELEASE: '曲包发布', SONG_ADD: '新曲追加',
    COLLABORATION: '联动', EVENT: '限时活动', MAINTENANCE: '维护',
  }[type]
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric',
  }).format(new Date(value))
}

onMounted(store.load)
</script>

<template>
  <div class="site-shell">
    <header class="topbar">
      <a class="brand" href="/">
        <span class="brand-mark"><span></span><span></span><span></span></span>
        <span>RHYTHM<br /><b>CALENDAR</b></span>
      </a>
      <div class="sync-state" :class="{ stale: store.status?.stale }">
        <i></i>{{ statusText }} · {{ lastUpdated }}
      </div>
    </header>

    <main>
      <section class="hero">
        <div>
          <p class="eyebrow">MUSIC GAME UPDATE TRACKER</p>
          <h1>不错过每一次<br /><em>节奏更新</em></h1>
          <p class="hero-copy">聚合音乐游戏官方公告，把版本、曲包与新曲更新放进一张清晰的日历。</p>
        </div>
        <div class="hero-stat">
          <span>{{ store.dynamics.length.toString().padStart(2, '0') }}</span>
          <p>已收录公告<br /><b>ARCAEA</b></p>
        </div>
      </section>

      <el-alert v-if="store.error" :title="store.error" type="error" show-icon :closable="false" />

      <section class="workspace" v-loading="store.loading">
        <div class="calendar-panel panel">
          <div class="section-heading">
            <div><el-icon><Calendar /></el-icon><span>更新日历</span></div>
            <button class="refresh-button" @click="store.load"><el-icon><Refresh /></el-icon>刷新</button>
          </div>
          <p class="calendar-note">优先按公告中提取的更新日期展示；未解析公告使用发布日期</p>
          <FullCalendar :options="calendarOptions" />
        </div>

        <aside class="feed-panel panel">
          <div class="section-heading">
            <div><el-icon><Connection /></el-icon><span>最新动态</span></div>
            <span class="game-chip">ARCAEA</span>
          </div>
          <div class="feed-list">
            <button v-for="item in store.dynamics.slice(0, 10)" :key="item.dynamic_id" class="feed-item" @click="openDynamic(item)">
              <span class="feed-date">{{ formatDate(item.publish_time) }}</span>
              <strong>{{ item.text.split('\n').find(Boolean) || 'Arcaea 官方公告' }}</strong>
              <span class="feed-more">查看公告 <el-icon><TopRight /></el-icon></span>
            </button>
            <div v-if="!store.loading && !store.dynamics.length" class="empty-state">尚无缓存数据</div>
          </div>
        </aside>
      </section>
    </main>

    <footer><span>RHYTHM CALENDAR · 2026</span><span>数据来自游戏官方公开账号</span></footer>

    <el-drawer v-model="detailOpen" size="min(520px, 92vw)" direction="rtl" class="detail-drawer">
      <template #header><span class="drawer-label">ARCAEA · 官方动态</span></template>
      <template v-if="selected">
        <div v-if="selectedEvent" class="event-summary">
          <span>{{ eventTypeLabel(selectedEvent.event_type) }}</span>
          <b>{{ formatDate(selectedEvent.event_date) }}<template v-if="selectedEvent.event_end_date"> — {{ formatDate(selectedEvent.event_end_date) }}</template></b>
        </div>
        <p class="detail-date">公告发布于 {{ formatDate(selected.publish_time) }}</p>
        <h2>{{ selected.text.split('\n').find(Boolean) }}</h2>
        <div class="detail-content">{{ selected.text }}</div>
        <a class="source-link" :href="selected.url" target="_blank" rel="noreferrer">在 Bilibili 查看原动态 <el-icon><TopRight /></el-icon></a>
      </template>
    </el-drawer>
  </div>
</template>
