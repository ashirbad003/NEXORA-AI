export interface SyncPushOperationPayload {
  op_id: string; // Idempotency key UUID
  action_type: 'SUBMIT_CARD_REVIEW' | 'RESOLVE_MISTAKE';
  client_timestamp: string;
  payload: Record<string, any>;
}

export interface SyncPushPayload {
  device_id: string;
  operations: SyncPushOperationPayload[];
}

export interface SyncOperationResult {
  op_id: string;
  status: 'SUCCESS' | 'SUPERSEDED' | 'REPLAYED' | 'REJECTED';
  message?: string | null;
  card_id?: string | null;
  repetition?: number | null;
  interval_days?: number | null;
  ease_factor?: number | null;
  stability?: number | null;
  next_review_at?: string | null;
  resulting_state_version?: number | null;
  is_replayed: boolean;
  is_superseded: boolean;
}

export interface SyncPushResponse {
  device_id: string;
  processed_count: number;
  results: SyncOperationResult[];
  new_server_seq: number;
}

export interface ChangeFeedItem {
  change_seq: number;
  entity_type: string;
  entity_id: string;
  operation: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface SyncPullResponse {
  server_seq: number;
  has_more: boolean;
  deltas: ChangeFeedItem[];
  tombstones: Array<Record<string, any>>;
}

export interface SyncSnapshotResponse {
  snapshot_seq: number;
  decks: Array<Record<string, any>>;
  due_cards: Array<Record<string, any>>;
  readiness_score: number;
}

export interface DeviceTokenRegisterPayload {
  device_id: string;
  expo_push_token: string;
  device_os: string;
  device_model?: string;
  app_version: string;
}

export interface DeviceTokenResponse {
  id: string;
  user_id: string;
  device_id: string;
  expo_push_token: string;
  device_os: string;
  device_model?: string | null;
  app_version: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string;
}
