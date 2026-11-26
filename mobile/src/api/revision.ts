import { apiClient } from './client';
import {
  FlashcardDeck,
  FlashcardItem,
  CardReviewSubmitPayload,
  CardReviewSubmitResult,
  RevisionDashboardStats,
  MistakeEntry,
} from './revisionTypes';
import { OfflineQueueService } from '../services/offlineQueue';

export const RevisionApi = {
  /**
   * Fetch user flashcard decks with counts.
   */
  async listDecks(category?: string): Promise<FlashcardDeck[]> {
    const params = category ? { category } : undefined;
    const res = await apiClient.get<FlashcardDeck[]>('/revision/decks', { params });
    return res.data;
  },

  /**
   * Fetch cards due for review across decks or within a specific deck.
   */
  async getDueCards(deckId?: string, limit: number = 50): Promise<FlashcardItem[]> {
    const params: Record<string, string | number> = { limit };
    if (deckId) params.deck_id = deckId;
    const res = await apiClient.get<FlashcardItem[]>('/revision/cards/due', { params });
    return res.data;
  },

  /**
   * Submit an individual card review.
   * If network fails, falls back gracefully to enqueuing for offline sync with user isolation.
   */
  async submitReview(payload: CardReviewSubmitPayload, userId: string = 'current'): Promise<CardReviewSubmitResult> {
    try {
      const res = await apiClient.post<CardReviewSubmitResult>('/revision/reviews/submit', payload);
      return res.data;
    } catch (error) {
      // Enqueue to user-isolated offline review queue if network/server issue
      await OfflineQueueService.enqueue({
        op_id: payload.idempotency_key,
        user_id: userId,
        card_id: payload.card_id,
        grade: payload.grade,
        time_spent_ms: payload.time_spent_ms,
        base_state_version: payload.base_state_version,
        client_timestamp: payload.client_reviewed_at || new Date().toISOString(),
      });
      throw error;
    }
  },

  /**
   * Fetch revision dashboard summary stats.
   */
  async getDashboardStats(timezone: string = 'UTC'): Promise<RevisionDashboardStats> {
    const res = await apiClient.get<RevisionDashboardStats>('/revision/dashboard/stats', {
      params: { timezone },
    });
    return res.data;
  },

  /**
   * Fetch mistake notebook entries.
   */
  async listMistakes(resolved?: boolean): Promise<MistakeEntry[]> {
    const params = resolved !== undefined ? { resolved } : undefined;
    const res = await apiClient.get<MistakeEntry[]>('/revision/mistakes', { params });
    return res.data;
  },

  /**
   * Mark a mistake as resolved.
   */
  async resolveMistake(mistakeId: string): Promise<MistakeEntry> {
    const res = await apiClient.post<MistakeEntry>(`/revision/mistakes/${mistakeId}/resolve`);
    return res.data;
  },

  /**
   * Flush pending offline review queue for current authenticated user.
   */
  async flushOfflineQueue(userId: string = 'current'): Promise<{ synced: number; failed: number }> {
    const queue = await OfflineQueueService.getQueue(userId);
    const pending = queue.filter((item) => item.status === 'PENDING' || item.status === 'FAILED');

    let synced = 0;
    let failed = 0;

    for (const item of pending) {
      try {
        await apiClient.post<CardReviewSubmitResult>('/revision/reviews/submit', {
          card_id: item.card_id,
          grade: item.grade,
          idempotency_key: item.op_id,
          time_spent_ms: item.time_spent_ms,
          base_state_version: item.base_state_version,
          client_reviewed_at: item.client_timestamp,
        });
        await OfflineQueueService.markSuccess(userId, item.op_id);
        synced += 1;
      } catch (err: any) {
        failed += 1;
        await OfflineQueueService.markFailure(userId, item.op_id, err?.message || 'Sync error');
      }
    }

    return { synced, failed };
  },
};
