import { OfflineQueueService, MAX_OFFLINE_QUEUE_CAPACITY, MAX_RETRY_CEILING, generateUUID } from '../services/offlineQueue';
import * as SecureStore from 'expo-secure-store';

jest.mock('expo-secure-store', () => {
  const store: Record<string, string> = {};
  return {
    setItemAsync: jest.fn(async (key: string, value: string) => {
      store[key] = value;
    }),
    getItemAsync: jest.fn(async (key: string) => {
      return store[key] || null;
    }),
    deleteItemAsync: jest.fn(async (key: string) => {
      delete store[key];
    }),
  };
});

describe('OfflineQueueService Advanced Integrity', () => {
  const userA = 'user_aaa_111';
  const userB = 'user_bbb_222';

  beforeEach(async () => {
    jest.clearAllMocks();
    await OfflineQueueService.clearQueue(userA);
    await OfflineQueueService.clearQueue(userB);
  });

  it('generates valid RFC4122 v4 UUIDs', () => {
    const uuid1 = generateUUID();
    const uuid2 = generateUUID();
    expect(uuid1).not.toBe(uuid2);
    expect(uuid1).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  });

  it('enforces strict cross-user queue isolation', async () => {
    await OfflineQueueService.enqueue({
      op_id: 'op_a1',
      user_id: userA,
      card_id: 'card_100',
      grade: 4,
      time_spent_ms: 1200,
      client_timestamp: new Date().toISOString(),
    });

    await OfflineQueueService.enqueue({
      op_id: 'op_b1',
      user_id: userB,
      card_id: 'card_200',
      grade: 5,
      time_spent_ms: 1500,
      client_timestamp: new Date().toISOString(),
    });

    const queueA = await OfflineQueueService.getQueue(userA);
    const queueB = await OfflineQueueService.getQueue(userB);

    expect(queueA.length).toBe(1);
    expect(queueA[0].user_id).toBe(userA);
    expect(queueA[0].card_id).toBe('card_100');

    expect(queueB.length).toBe(1);
    expect(queueB[0].user_id).toBe(userB);
    expect(queueB[0].card_id).toBe('card_200');

    expect(await OfflineQueueService.getPendingCount(userA)).toBe(1);
    expect(await OfflineQueueService.getPendingCount(userB)).toBe(1);
  });

  it('enforces non-destructive capacity ceiling (rejecting when 200 pending, evicting failed) and tracks retry count', async () => {
    // Fill to capacity with pending items
    for (let i = 0; i < MAX_OFFLINE_QUEUE_CAPACITY; i++) {
      await OfflineQueueService.enqueue({
        op_id: `op_${i}`,
        user_id: userA,
        card_id: `card_${i}`,
        grade: 3,
        time_spent_ms: 1000,
        client_timestamp: new Date().toISOString(),
      });
    }

    let queue = await OfflineQueueService.getQueue(userA);
    expect(queue.length).toBe(MAX_OFFLINE_QUEUE_CAPACITY);

    // Attempting to add 201st pending item throws explicit non-destructive QUEUE_FULL error
    await expect(
      OfflineQueueService.enqueue({
        op_id: 'op_overflow',
        user_id: userA,
        card_id: 'card_overflow',
        grade: 4,
        time_spent_ms: 1000,
        client_timestamp: new Date().toISOString(),
      })
    ).rejects.toThrow('QUEUE_FULL');

    // If an item has failed past retry ceiling, it becomes evictable
    for (let r = 0; r < MAX_RETRY_CEILING; r++) {
      await OfflineQueueService.markFailure(userA, 'op_0', '503 Service Unavailable');
    }

    queue = await OfflineQueueService.getQueue(userA);
    expect(queue[0].status).toBe('FAILED');
    expect(queue[0].retry_count).toBe(MAX_RETRY_CEILING);

    // Now adding an item evicts the permanently failed item without discarding pending reviews
    await OfflineQueueService.enqueue({
      op_id: 'op_overflow_allowed',
      user_id: userA,
      card_id: 'card_overflow_allowed',
      grade: 4,
      time_spent_ms: 1000,
      client_timestamp: new Date().toISOString(),
    });

    queue = await OfflineQueueService.getQueue(userA);
    expect(queue.length).toBe(MAX_OFFLINE_QUEUE_CAPACITY);
    expect(queue.some((q) => q.op_id === 'op_overflow_allowed')).toBe(true);
    expect(queue.some((q) => q.op_id === 'op_0')).toBe(false);
  });

  it('clears specific user queue on logout without impacting other accounts', async () => {
    await OfflineQueueService.enqueue({
      op_id: 'op_a',
      user_id: userA,
      card_id: 'c1',
      grade: 4,
      time_spent_ms: 1000,
      client_timestamp: new Date().toISOString(),
    });

    await OfflineQueueService.enqueue({
      op_id: 'op_b',
      user_id: userB,
      card_id: 'c2',
      grade: 5,
      time_spent_ms: 1000,
      client_timestamp: new Date().toISOString(),
    });

    await OfflineQueueService.clearQueue(userA);

    expect(await OfflineQueueService.getQueue(userA)).toEqual([]);
    const queueB = await OfflineQueueService.getQueue(userB);
    expect(queueB.length).toBe(1);
    expect(queueB[0].op_id).toBe('op_b');
  });
});
