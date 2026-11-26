import { RevisionApi } from '../api/revision';
import { apiClient } from '../api/client';
import { OfflineQueueService } from '../services/offlineQueue';

jest.mock('../api/client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

jest.mock('../services/offlineQueue', () => ({
  OfflineQueueService: {
    enqueue: jest.fn(),
    getQueue: jest.fn(),
    markSuccess: jest.fn(),
    markFailure: jest.fn(),
    getPendingCount: jest.fn(),
  },
}));

describe('RevisionApi Integration Contracts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('listDecks calls /revision/decks and returns array', async () => {
    const mockDecks = [
      {
        id: 'deck_1',
        user_id: 'u1',
        title: 'Binary Trees',
        category: 'DSA',
        tags: ['tree', 'graph'],
        is_public: true,
        is_system: false,
        card_count: 10,
        due_card_count: 3,
        created_at: '2026-11-26T00:00:00Z',
        updated_at: '2026-11-26T00:00:00Z',
      },
    ];

    (apiClient.get as jest.Mock).mockResolvedValue({ data: mockDecks });

    const decks = await RevisionApi.listDecks();
    expect(apiClient.get).toHaveBeenCalledWith('/revision/decks', { params: undefined });
    expect(decks.length).toBe(1);
    expect(decks[0].title).toBe('Binary Trees');
  });

  it('submitReview passes userId to OfflineQueueService on network fault', async () => {
    (apiClient.post as jest.Mock).mockRejectedValue(new Error('Network Error'));

    await expect(
      RevisionApi.submitReview(
        {
          card_id: 'card_xyz',
          grade: 4,
          idempotency_key: 'rev_uuid_12345',
          time_spent_ms: 2200,
        },
        'user_test_999'
      )
    ).rejects.toThrow('Network Error');

    expect(OfflineQueueService.enqueue).toHaveBeenCalledWith(
      expect.objectContaining({
        user_id: 'user_test_999',
        card_id: 'card_xyz',
        grade: 4,
        op_id: 'rev_uuid_12345',
      })
    );
  });

  it('flushOfflineQueue reconciles pending queue with backend and clears success entries', async () => {
    const mockQueue = [
      {
        op_id: 'op_flush_1',
        user_id: 'user_test_999',
        card_id: 'card_1',
        grade: 4,
        time_spent_ms: 1000,
        client_timestamp: '2026-11-26T12:00:00Z',
        status: 'PENDING',
        retry_count: 0,
      },
      {
        op_id: 'op_flush_2',
        user_id: 'user_test_999',
        card_id: 'card_2',
        grade: 1,
        time_spent_ms: 1500,
        client_timestamp: '2026-11-26T12:01:00Z',
        status: 'PENDING',
        retry_count: 0,
      },
    ];

    (OfflineQueueService.getQueue as jest.Mock).mockResolvedValue(mockQueue);
    (apiClient.post as jest.Mock)
      .mockResolvedValueOnce({ data: { is_replayed: false } }) // first succeeds
      .mockRejectedValueOnce(new Error('500 Internal Error')); // second fails

    const flushResult = await RevisionApi.flushOfflineQueue('user_test_999');

    expect(flushResult.synced).toBe(1);
    expect(flushResult.failed).toBe(1);
    expect(OfflineQueueService.markSuccess).toHaveBeenCalledWith('user_test_999', 'op_flush_1');
    expect(OfflineQueueService.markFailure).toHaveBeenCalledWith('user_test_999', 'op_flush_2', expect.any(String));
  });

  it('resolveMistake calls /revision/mistakes/{id}/resolve', async () => {
    const mockResolved = {
      id: 'mistake_99',
      user_id: 'u1',
      source_type: 'coding',
      title: 'Off-by-one boundary',
      tags: ['array'],
      is_resolved: true,
      resolved_at: '2026-11-26T12:05:00Z',
      created_at: '2026-11-26T10:00:00Z',
    };

    (apiClient.post as jest.Mock).mockResolvedValue({ data: mockResolved });

    const result = await RevisionApi.resolveMistake('mistake_99');
    expect(apiClient.post).toHaveBeenCalledWith('/revision/mistakes/mistake_99/resolve');
    expect(result.is_resolved).toBe(true);
  });
});
