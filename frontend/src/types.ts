export interface Game {
  id: number
  name: string
  display_name: string
  enabled: boolean
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

export interface FetchStatus {
  last_attempt_at: string | null
  last_success_at: string | null
  last_error: string | null
  stale: boolean
}

export interface StaticSnapshot {
  generated_at: string
  games: Game[]
  dynamics: DynamicItem[]
  status: FetchStatus
}
