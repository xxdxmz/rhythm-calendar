export interface Game {
  id: number
  name: string
  display_name: string
  enabled: boolean
  official: boolean
  theme_color: string
}

export interface DynamicItem {
  dynamic_id: string
  game: string
  uid: string
  text: string
  publish_time: string
  url: string
  dynamic_type: string
  fetched_at: string
}

export interface EventItem {
  id: string
  game: string
  source_dynamic_id: string
  title: string
  description: string
  event_type: 'VERSION_UPDATE' | 'PACK_RELEASE' | 'SONG_ADD' | 'COLLABORATION' | 'EVENT' | 'MAINTENANCE'
  event_date: string
  event_end_date?: string
  url: string
  status: 'AUTO_PARSED' | 'REVIEWED'
}

export interface FetchStatus {
  last_attempt_at: string | null
  last_success_at: string | null
  last_error: string | null
  stale: boolean
  partial_failure?: boolean
  sources?: Array<{
    source: string
    last_attempt_at: string
    last_success_at: string | null
    last_error: string | null
  }>
}

export interface StaticSnapshot {
  generated_at: string
  games: Game[]
  dynamics: DynamicItem[]
  events?: EventItem[]
  status: FetchStatus
}
