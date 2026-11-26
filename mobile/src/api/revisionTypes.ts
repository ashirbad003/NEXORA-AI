export interface FlashcardDeck {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  category: string;
  tags: string[];
  is_public: boolean;
  is_system: boolean;
  card_count: number;
  due_card_count: number;
  created_at: string;
  updated_at: string;
}

export interface FlashcardItem {
  id: string;
  deck_id: string;
  prompt: string;
  answer: string;
  explanation?: string | null;
  code_snippet?: string | null;
  audio_url?: string | null;
  order_index: number;
  created_at: string;
  repetition?: number;
  interval_days?: number;
  ease_factor?: number;
  stability?: number;
  next_review_at?: string | null;
  is_due: boolean;
}

export interface CardReviewSubmitPayload {
  card_id: string;
  grade: number; // 0..5
  idempotency_key: string;
  session_id?: string;
  time_spent_ms: number;
  user_timezone?: string;
  base_state_version?: number;
  device_id?: string;
  client_reviewed_at?: string;
}

export interface CardReviewSubmitResult {
  idempotency_key: string;
  card_id: string;
  submitted_grade: number;
  repetition: number;
  interval_days: number;
  ease_factor: number;
  stability: number;
  next_review_at: string;
  is_replayed: boolean;
  is_superseded: boolean;
  resulting_state_version?: number;
}

export interface HeatmapDay {
  date: string;
  count: number;
}

export interface RevisionDashboardStats {
  total_decks: number;
  total_cards: number;
  due_cards_count: number;
  cards_reviewed_today: number;
  retention_rate_pct: number;
  current_streak_days: number;
  heatmap: HeatmapDay[];
}

export interface MistakeEntry {
  id: string;
  user_id: string;
  source_type: 'manual' | 'coding' | 'assessment';
  source_id?: string | null;
  title: string;
  question_context?: string | null;
  submitted_answer?: string | null;
  expected_answer?: string | null;
  error_message?: string | null;
  tags: string[];
  is_resolved: boolean;
  resolved_at?: string | null;
  created_at: string;
}
