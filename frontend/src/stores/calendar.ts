import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { DynamicItem, FetchStatus, Game, StaticSnapshot } from '../types'

const staticDataUrl = import.meta.env.VITE_STATIC_DATA_URL as string | undefined

export const useCalendarStore = defineStore('calendar', () => {
  const games = ref<Game[]>([])
  const dynamics = ref<DynamicItem[]>([])
  const status = ref<FetchStatus | null>(null)
  const loading = ref(false)
  const error = ref('')

  const calendarEvents = computed(() =>
    dynamics.value.map((item) => ({
      id: item.dynamic_id,
      title: item.text.split('\n').find(Boolean)?.slice(0, 30) || 'Arcaea 公告',
      start: item.publish_time,
      allDay: true,
      backgroundColor: '#7457ff',
      borderColor: '#8e7aff',
      extendedProps: item,
    })),
  )

  function applySnapshot(snapshot: StaticSnapshot) {
    games.value = snapshot.games
    dynamics.value = snapshot.dynamics
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

  return { games, dynamics, status, loading, error, calendarEvents, load }
})
