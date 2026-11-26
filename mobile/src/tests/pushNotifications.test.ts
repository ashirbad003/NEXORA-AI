import { PushNotificationService } from '../services/pushNotifications';
import { SyncApi } from '../api/sync';
import { SyncEngineService } from '../services/syncEngine';

jest.mock('../api/sync', () => ({
  SyncApi: {
    registerDeviceToken: jest.fn(),
  },
}));

jest.mock('../services/syncEngine', () => ({
  SyncEngineService: {
    getOrCreateDeviceId: jest.fn(() => Promise.resolve('device_mock_xyz_12345')),
  },
}));

describe('PushNotificationService', () => {
  it('registers device push token with backend /notifications/devices/register', async () => {
    (SyncApi.registerDeviceToken as jest.Mock).mockResolvedValue({
      id: 'dt_1',
      device_id: 'device_mock_xyz_12345',
      expo_push_token: 'simulated_expo_push_token_device_m',
      is_active: true,
    });

    const status = await PushNotificationService.registerForPushNotifications('user_student_1');

    expect(status.isRegistered).toBe(true);
    expect(SyncApi.registerDeviceToken).toHaveBeenCalledWith(
      expect.objectContaining({
        device_id: 'device_mock_xyz_12345',
        device_os: 'ANDROID',
        app_version: '1.0.0',
      })
    );
  });
});
