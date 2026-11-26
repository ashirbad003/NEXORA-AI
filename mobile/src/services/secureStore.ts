import * as SecureStore from 'expo-secure-store';

const KEY_ACCESS_TOKEN = 'nexora_auth_access_token';
const KEY_REFRESH_TOKEN = 'nexora_auth_refresh_token';
const KEY_USER_CACHE = 'nexora_auth_user_cache';
const KEY_BIOMETRIC_ENABLED = 'nexora_biometric_enabled';

/**
 * Secure Store Service
 * Stores authentication tokens and biometric preferences using hardware-backed SecureStore.
 * Plaintext storage (such as unencrypted localStorage or AsyncStorage) is strictly avoided.
 */
export const SecureStoreService = {
  async saveTokens(accessToken: string, refreshToken: string): Promise<void> {
    await SecureStore.setItemAsync(KEY_ACCESS_TOKEN, accessToken);
    await SecureStore.setItemAsync(KEY_REFRESH_TOKEN, refreshToken);
  },

  async getAccessToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(KEY_ACCESS_TOKEN);
    } catch {
      return null;
    }
  },

  async getRefreshToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(KEY_REFRESH_TOKEN);
    } catch {
      return null;
    }
  },

  async saveCachedUser(userJson: string): Promise<void> {
    await SecureStore.setItemAsync(KEY_USER_CACHE, userJson);
  },

  async getCachedUser(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(KEY_USER_CACHE);
    } catch {
      return null;
    }
  },

  async setBiometricEnabled(enabled: boolean): Promise<void> {
    await SecureStore.setItemAsync(KEY_BIOMETRIC_ENABLED, enabled ? 'true' : 'false');
  },

  async isBiometricEnabled(): Promise<boolean> {
    try {
      const val = await SecureStore.getItemAsync(KEY_BIOMETRIC_ENABLED);
      return val === 'true';
    } catch {
      return false;
    }
  },

  async clearAllCredentials(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(KEY_ACCESS_TOKEN);
      await SecureStore.deleteItemAsync(KEY_REFRESH_TOKEN);
      await SecureStore.deleteItemAsync(KEY_USER_CACHE);
    } catch {
      // Ignore deletion errors on already removed keys
    }
  },
};
