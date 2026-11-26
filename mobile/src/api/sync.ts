import { apiClient } from './client';
import {
  SyncPushPayload,
  SyncPushResponse,
  SyncPullResponse,
  SyncSnapshotResponse,
  DeviceTokenRegisterPayload,
  DeviceTokenResponse,
} from './syncTypes';

export const SyncApi = {
  /**
   * Pushes a batch of offline review or learning actions to the server.
   */
  async pushOperations(payload: SyncPushPayload): Promise<SyncPushResponse> {
    const res = await apiClient.post<SyncPushResponse>('/sync/push', payload);
    return res.data;
  },

  /**
   * Pulls incremental deltas from the change feed after `since_seq`.
   */
  async pullDeltas(deviceId: string, sinceSeq: number = 0, limit: number = 50): Promise<SyncPullResponse> {
    const res = await apiClient.get<SyncPullResponse>('/sync/pull', {
      params: { device_id: deviceId, since_seq: sinceSeq, limit },
    });
    return res.data;
  },

  /**
   * Fetches a full snapshot for a newly registered device or after cursor expiration.
   */
  async getSnapshot(deviceId: string): Promise<SyncSnapshotResponse> {
    const res = await apiClient.get<SyncSnapshotResponse>('/sync/snapshot', {
      params: { device_id: deviceId },
    });
    return res.data;
  },

  /**
   * Registers or updates an Expo push token for this device with cross-user isolation.
   */
  async registerDeviceToken(payload: DeviceTokenRegisterPayload): Promise<DeviceTokenResponse> {
    const res = await apiClient.post<DeviceTokenResponse>('/notifications/devices/register', payload);
    return res.data;
  },
};
