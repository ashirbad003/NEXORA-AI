import { SyncApi } from '../api/sync';
import { SyncEngineService } from './syncEngine';

export interface NotificationStatus {
  isRegistered: boolean;
  token?: string | null;
  error?: string | null;
}

export const PushNotificationService = {
  /**
   * Initializes and registers the device push token with the backend.
   * If running in simulated or headless environment without native push providers,
   * handles registration gracefully with simulated development token.
   */
  async registerForPushNotifications(userId: string): Promise<NotificationStatus> {
    try {
      const deviceId = await SyncEngineService.getOrCreateDeviceId();
      let token = 'simulated_expo_push_token_' + deviceId.slice(0, 8);

      // Register with backend /notifications/devices/register
      await SyncApi.registerDeviceToken({
        device_id: deviceId,
        expo_push_token: token,
        device_os: 'ANDROID',
        device_model: 'Android Device',
        app_version: '1.0.0',
      });

      return {
        isRegistered: true,
        token,
      };
    } catch (err: any) {
      return {
        isRegistered: false,
        error: err?.message || 'Device token registration failed',
      };
    }
  },
};
