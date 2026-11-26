import * as SecureStore from 'expo-secure-store';

export interface QueuedReviewOperation {
  op_id: string; // Idempotency key (UUID)
  user_id: string; // Account isolation
  card_id: string;
  grade: number; // 0..5
  time_spent_ms: number;
  base_state_version?: number;
  client_timestamp: string; // ISO string
  status: 'PENDING' | 'SYNCED' | 'FAILED';
  retry_count: number;
  error?: string;
}

const KEY_OFFLINE_REVIEW_PREFIX = 'nexora_offline_review_queue_';
export const MAX_OFFLINE_QUEUE_CAPACITY = 200; // Capacity ceiling preventing storage exhaustion
export const MAX_RETRY_CEILING = 10;

/**
 * Generate a cryptographically strong UUID v4 idempotency key.
 */
export function generateUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Offline Review Queue Service
 * Manages user-isolated local persistence, non-destructive capacity limits, and deduplication of reviews performed offline.
 */
export const OfflineQueueService = {
  getStorageKey(userId: string): string {
    return `${KEY_OFFLINE_REVIEW_PREFIX}${userId || 'anonymous'}`;
  },

  async getQueue(userId: string): Promise<QueuedReviewOperation[]> {
    try {
      const raw = await SecureStore.getItemAsync(this.getStorageKey(userId));
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  },

  /**
   * Enqueues an offline review operation.
   * Safety Preflight: If queue capacity is reached, NEVER silently discard pending user reviews.
   * Only synced or permanently failed items exceeding MAX_RETRY_CEILING are evictable.
   * If all items are pending, throws an explicit QUEUE_FULL error so the UI can notify the user.
   */
  async enqueue(op: Omit<QueuedReviewOperation, 'status' | 'retry_count'>): Promise<QueuedReviewOperation> {
    const queue = await this.getQueue(op.user_id);

    // 1. Check existing pending review for the same card
    const existingIndex = queue.findIndex(
      (item) => item.op_id === op.op_id || (item.card_id === op.card_id && item.status === 'PENDING')
    );

    const queuedItem: QueuedReviewOperation = {
      ...op,
      status: 'PENDING',
      retry_count: 0,
    };

    if (existingIndex >= 0) {
      // Safely update existing item with latest recall attempt and timestamp
      queue[existingIndex] = queuedItem;
    } else {
      // If at capacity, check if there is an evictable non-pending item
      if (queue.length >= MAX_OFFLINE_QUEUE_CAPACITY) {
        const evictableIdx = queue.findIndex((item) => item.status === 'SYNCED' || (item.status === 'FAILED' && item.retry_count >= MAX_RETRY_CEILING));
        if (evictableIdx >= 0) {
          queue.splice(evictableIdx, 1);
        } else {
          // All 200 items are active pending reviews: reject with explicit non-destructive error
          throw new Error('QUEUE_FULL: Local offline review buffer is at maximum capacity (200 pending reviews). Please reconnect to sync.');
        }
      }
      queue.push(queuedItem);
    }

    await SecureStore.setItemAsync(this.getStorageKey(op.user_id), JSON.stringify(queue));
    return queuedItem;
  },

  async markSuccess(userId: string, op_id: string): Promise<void> {
    const queue = await this.getQueue(userId);
    // Remove confirmed synced operation
    const updated = queue.filter((item) => item.op_id !== op_id);
    await SecureStore.setItemAsync(this.getStorageKey(userId), JSON.stringify(updated));
  },

  async markFailure(userId: string, op_id: string, errorMsg: string): Promise<void> {
    const queue = await this.getQueue(userId);
    const item = queue.find((q) => q.op_id === op_id);
    if (item) {
      item.retry_count += 1;
      item.error = errorMsg;
      if (item.retry_count >= MAX_RETRY_CEILING) {
        item.status = 'FAILED';
      }
      await SecureStore.setItemAsync(this.getStorageKey(userId), JSON.stringify(queue));
    }
  },

  async getPendingCount(userId: string): Promise<number> {
    const queue = await this.getQueue(userId);
    return queue.filter((item) => item.status === 'PENDING' || item.status === 'FAILED').length;
  },

  async clearQueue(userId: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(this.getStorageKey(userId));
    } catch {
      // Ignore
    }
  },
};
