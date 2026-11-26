import * as SecureStore from 'expo-secure-store';
import { SyncApi } from '../api/sync';
import { OfflineQueueService, QueuedReviewOperation, generateUUID } from './offlineQueue';

const KEY_DEVICE_ID = 'nexora_mobile_device_uuid';
const KEY_LAST_SYNCED_SEQ = 'nexora_last_synced_sequence_';

export interface SyncResult {
  pushedCount: number;
  supersededCount: number;
  replayedCount: number;
  rejectedCount: number;
  pulledDeltasCount: number;
  newServerSeq: number;
}

export const SyncEngineService = {
  /**
   * Retrieves or provisions a persistent hardware device UUID for this mobile installation.
   */
  async getOrCreateDeviceId(): Promise<string> {
    try {
      let deviceId = await SecureStore.getItemAsync(KEY_DEVICE_ID);
      if (!deviceId) {
        deviceId = generateUUID();
        await SecureStore.setItemAsync(KEY_DEVICE_ID, deviceId);
      }
      return deviceId;
    } catch {
      return generateUUID();
    }
  },

  /**
   * Gets the last acknowledged server sequence number for a user on this device.
   */
  async getLastSyncedSeq(userId: string): Promise<number> {
    try {
      const val = await SecureStore.getItemAsync(`${KEY_LAST_SYNCED_SEQ}${userId}`);
      return val ? parseInt(val, 10) : 0;
    } catch {
      return 0;
    }
  },

  /**
   * Updates the last acknowledged server sequence number for a user on this device.
   */
  async setLastSyncedSeq(userId: string, seq: number): Promise<void> {
    await SecureStore.setItemAsync(`${KEY_LAST_SYNCED_SEQ}${userId}`, seq.toString());
  },

  /**
   * Performs full bidirectional synchronization:
   * 1. Pushes pending local offline review operations to /sync/push.
   * 2. Reconciles results (SUPERSEDED, REPLAYED, SUCCESS, REJECTED).
   * 3. Pulls latest server deltas from /sync/pull after last synced seq.
   * 4. Updates last synced seq watermark.
   */
  async synchronize(userId: string): Promise<SyncResult> {
    const deviceId = await this.getOrCreateDeviceId();
    const queue = await OfflineQueueService.getQueue(userId);
    const pendingOps = queue.filter((item) => item.status === 'PENDING' || item.status === 'FAILED');

    let pushed = 0;
    let superseded = 0;
    let replayed = 0;
    let rejected = 0;
    let pulledCount = 0;
    let serverSeq = await this.getLastSyncedSeq(userId);

    // 1. Push Phase: Send pending offline actions to /sync/push in batches of 50
    if (pendingOps.length > 0) {
      const batch = pendingOps.slice(0, 50).map((op) => ({
        op_id: op.op_id,
        action_type: 'SUBMIT_CARD_REVIEW' as const,
        client_timestamp: op.client_timestamp,
        payload: {
          card_id: op.card_id,
          grade: op.grade,
          time_spent_ms: op.time_spent_ms,
          base_state_version: op.base_state_version,
        },
      }));

      try {
        const pushRes = await SyncApi.pushOperations({
          device_id: deviceId,
          operations: batch,
        });

        serverSeq = pushRes.new_server_seq;

        for (const res of pushRes.results) {
          if (res.status === 'SUCCESS') {
            pushed += 1;
            await OfflineQueueService.markSuccess(userId, res.op_id);
          } else if (res.status === 'SUPERSEDED') {
            superseded += 1;
            // A newer review already advanced active state; clear pending item without overwriting
            await OfflineQueueService.markSuccess(userId, res.op_id);
          } else if (res.status === 'REPLAYED') {
            replayed += 1;
            await OfflineQueueService.markSuccess(userId, res.op_id);
          } else if (res.status === 'REJECTED') {
            rejected += 1;
            await OfflineQueueService.markFailure(userId, res.op_id, res.message || 'Operation rejected');
          }
        }
      } catch (pushErr: any) {
        // Record failure for pending batch
        for (const op of batch) {
          await OfflineQueueService.markFailure(userId, op.op_id, pushErr?.message || 'Network push error');
        }
        throw pushErr;
      }
    }

    // 2. Pull Phase: Fetch incremental deltas since last sequence
    try {
      const pullRes = await SyncApi.pullDeltas(deviceId, serverSeq, 50);
      pulledCount = pullRes.deltas.length;
      serverSeq = pullRes.server_seq;
      await this.setLastSyncedSeq(userId, serverSeq);
    } catch (pullErr: any) {
      // If 410 Gone (retention expired), pull fresh snapshot
      if (pullErr?.response?.status === 410) {
        const snap = await SyncApi.getSnapshot(deviceId);
        serverSeq = snap.snapshot_seq;
        await this.setLastSyncedSeq(userId, serverSeq);
      }
    }

    return {
      pushedCount: pushed,
      supersededCount: superseded,
      replayedCount: replayed,
      rejectedCount: rejected,
      pulledDeltasCount: pulledCount,
      newServerSeq: serverSeq,
    };
  },
};
