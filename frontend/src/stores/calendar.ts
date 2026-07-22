import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { DynamicItem, EventItem, FetchStatus, Game, StaticSnapshot } from '../types'

const staticDataUrl = import.meta.env.VITE_STATIC_DATA_URL as string | undefined
const eventLabels: Record<EventItem['event_type'], string> = {
  VERSION_UPDATE: '版本', PACK_RELEASE: '曲包', SONG_ADD: '新曲',
  COLLABORATION: '联动', EVENT: '活动', MAINTENANCE: '维护',
}
const eventColors: Record<EventItem['event_type'], string> = {
  VERSION_UPDATE: '#3f8cff', PACK_RELEASE: '#7457ff', SONG_ADD: '#db5cff',
  COLLABORATION: '#ff7a45', EVENT: '#20bfa9', MAINTENANCE: '#7b8194',
}
const isProjectSekai = (game: string) => game === '世界计划日服资讯' || game === '世界计划国服'

export const useCalendarStore = defineStore('calendar', () => {
  const games = ref<Game[]>([])
  const dynamics = ref<DynamicItem[]>([])
  const events = ref<EventItem[]>([])
  const status = ref<FetchStatus | null>(null)
  const activeGame = ref('all')
  const loading = ref(false)
  const error = ref('')

  const filteredDynamics = computed(() => activeGame.value === 'all'
    ? dynamics.value
    : dynamics.value.filter((item) => item.game === activeGame.value))
  const filteredEvents = computed(() => activeGame.value === 'all'
    ? events.value
    : events.value.filter((item) => item.game === activeGame.value))

  function gameColor(gameName: string) {
    return games.value.find((game) => game.display_name === gameName)?.theme_color || '#7457ff'
  }

  const calendarEvents = computed(() => {
    const parsedDynamicIds = new Set(filteredEvents.value.map((item) => item.source_dynamic_id))
    const fallbackEvents = filteredDynamics.value
      .filter((item) => !parsedDynamicIds.has(item.dynamic_id))
      .map((item) => ({
        id: item.dynamic_id,
        title: `${item.game} · ${item.text.split('\n').find(Boolean)?.slice(0, 24) || '公告'}`,
        start: item.publish_time,
        allDay: true,
        backgroundColor: gameColor(item.game),
        borderColor: gameColor(item.game),
        extendedProps: {
          source_dynamic_id: item.dynamic_id,
          display_priority: isProjectSekai(item.game) ? 10 : 0,
        },
      }))
    const parsedEvents = filteredEvents.value.map((item) => ({
      id: item.id,
      title: `${item.game} · [${eventLabels[item.event_type]}] ${item.title.slice(0, 20)}`,
      start: item.event_date,
      allDay: true,
      backgroundColor: activeGame.value === 'all' ? gameColor(item.game) : eventColors[item.event_type],
      borderColor: activeGame.value === 'all' ? gameColor(item.game) : eventColors[item.event_type],
      extendedProps: {
        ...item,
        display_priority: isProjectSekai(item.game) ? 10 : 0,
      },
    }))
    return [...parsedEvents, ...fallbackEvents]
  })

  function applySnapshot(snapshot: StaticSnapshot) {
    games.value = snapshot.games
    dynamics.value = snapshot.dynamics
    events.value = snapshot.events || []
    status.value = snapshot.status
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      if (staticDataUrl) {
        applySnapshot((await api.get<StaticSnapshot>(staticDataUrl)).data)
        return
      }
      const [gameResponse, dynamicResponse, statusResponse] = await Promise.all([
        api.get<Game[]>('/api/games'),
        api.get<DynamicItem[]>('/api/dynamics/latest', { params: { limit: 50 } }),
        api.get<FetchStatus>('/api/dynamics/status'),
      ])
      games.value = gameResponse.data
      dynamics.value = dynamicResponse.data
      status.value = statusResponse.data
    } catch (reason) {
      try {
        applySnapshot((await api.get<StaticSnapshot>('/data/snapshot.json')).data)
      } catch {
        error.value = reason instanceof Error ? reason.message : '数据加载失败'
      }
    } finally {
      loading.value = false
    }
  }

  return {
    games, dynamics, events, status, loading, error, activeGame,
    filteredDynamics, filteredEvents, calendarEvents, load,
  }
})
