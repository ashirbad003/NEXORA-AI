import { SecureStoreService } from '../services/secureStore';
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

describe('SecureStoreService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('saves and retrieves access and refresh tokens correctly', async () => {
    await SecureStoreService.saveTokens('mock_access_123', 'mock_refresh_456');

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('nexora_auth_access_token', 'mock_access_123');
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('nexora_auth_refresh_token', 'mock_refresh_456');

    const access = await SecureStoreService.getAccessToken();
    const refresh = await SecureStoreService.getRefreshToken();

    expect(access).toBe('mock_access_123');
    expect(refresh).toBe('mock_refresh_456');
  });

  it('saves, reads, and toggles biometric preference', async () => {
    await SecureStoreService.setBiometricEnabled(true);
    let enabled = await SecureStoreService.isBiometricEnabled();
    expect(enabled).toBe(true);

    await SecureStoreService.setBiometricEnabled(false);
    enabled = await SecureStoreService.isBiometricEnabled();
    expect(enabled).toBe(false);
  });

  it('clears all credentials upon logout', async () => {
    await SecureStoreService.saveTokens('access_to_delete', 'refresh_to_delete');
    await SecureStoreService.clearAllCredentials();

    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('nexora_auth_access_token');
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('nexora_auth_refresh_token');
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('nexora_auth_user_cache');

    const access = await SecureStoreService.getAccessToken();
    expect(access).toBeNull();
  });
});
