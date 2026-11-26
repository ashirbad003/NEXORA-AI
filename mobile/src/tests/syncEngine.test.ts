import { SyncEngineService } from '../services/syncEngine';
import { SyncApi } from '../api/sync';
import { OfflineQueueService } from '../services/offlineQueue';
import * as SecureStore from 'expo-secure-store';

jest.mock('../api/sync', () => ({
  SyncApi: {
    pushOperations: jest.fn(),
    pullDeltas: jest.fn(),
    getSnapshot: jest.fn(),
    registerDeviceToken: jest.fn(),
  },
}));

jest.mock('../services/offlineQueue', () => ({
  OfflineQueueService: {
    getQueue: jest.fn(),
    markSuccess: jest.fn(),
    markFailure: jest.fn(),
  },
  generateUUID: jest.fn(() => 'mock-device-uuid-1234'),
}));

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

describe('SyncEngineService', () => {
  const userId = 'user_sync_test';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('generates and persists hardware device UUID', async () => {
    const deviceId = await SyncEngineService.getOrCreateDeviceId();
    expect(deviceId).toBe('mock-device-uuid-1234');
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('nexora_mobile_device_uuid', 'mock-device-uuid-1234');
  });

  it('executes push phase, processes SUPERSEDED and SUCCESS operations, and updates seq watermark', async () => {
    const mockPendingOps = [
      {
        op_id: 'op_1',
        user_id: userId,
        card_id: 'card_10',
        grade: 4,
        time_spent_ms: 1000,
        client_timestamp: '2026-11-26T12:00:00Z',
        status: 'PENDING' as const,
        retry_count: 0,
      },
      {
        op_id: 'op_2',
        user_id: userId,
        card_id: 'card_20',
        grade: 2,
        time_spent_ms: 2000,
        client_timestamp: '2026-11-26T12:01:00Z',
        status: 'PENDING' as const,
        retry_count: 0,
      },
    ];

    (OfflineQueueService.getQueue as jest.Mock).mockResolvedValue(mockPendingOps);

    (SyncApi.pushOperations as jest.Mock).mockResolvedValue({
      device_id: 'mock-device-uuid-1234',
      processed_count: 2,
      results: [
        { op_id: 'op_1', status: 'SUCCESS' },
        { op_id: 'op_2', status: 'SUPERSEDED', message: 'Card schedule was already advanced' },
      ],
      new_server_seq: 105,
    });

    (SyncApi.pullDeltas as jest.Mock).mockResolvedValue({
      server_seq: 108,
      has_more: false,
      deltas: [
        {
          change_seq: 106,
          entity_type: 'card_review',
          entity_id: 'cr_1',
          operation: 'UPDATE',
          payload: {},
          created_at: '2026-11-26T12:05:00Z',
        },
      ],
      tombstones: [],
    });

    const res = await SyncEngineService.synchronize(userId);

    expect(res.pushedCount).toBe(1);
    expect(res.supersededCount).toBe(1);
    expect(res.pulledDeltasCount).toBe(1);
    expect(res.newServerSeq).toBe(108);

    expect(OfflineQueueService.markSuccess).toHaveBeenCalledWith(userId, 'op_1');
    expect(OfflineQueueService.markSuccess).toHaveBeenCalledWith(userId, 'op_2');
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(`nexora_last_synced_sequence_${userId}`, '108');
  });

  it('recovers from HTTP 410 retention expiry by requesting snapshot', async () => {
    (OfflineQueueService.getQueue as jest.Mock).mockResolvedValue([]);
    (SyncApi.pullDeltas as jest.Mock).mockRejectedValue({
      response: { status: 410 },
    });
    (SyncApi.getSnapshot as jest.Mock).mockResolvedValue({
      snapshot_seq: 200,
      decks: [],
      due_cards: [],
      readiness_score: 85,
    });

    const res = await SyncEngineService.synchronize(userId);

    expect(SyncApi.getSnapshot).toHaveBeenCalled();
    expect(res.newServerSeq).toBe(200);
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(`nexora_last_synced_sequence_${userId}`, '200');
  });
});
