import { apiClient } from './client';
import {
  LoginPayload,
  StudentRegisterPayload,
  TokenResponse,
  User,
} from './types';
import { SecureStoreService } from '../services/secureStore';

export const AuthApi = {
  /**
   * Authenticate student with email and password.
   */
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/auth/login', payload);
    const data = response.data;
    await SecureStoreService.saveTokens(data.access_token, data.refresh_token);
    await SecureStoreService.saveCachedUser(JSON.stringify(data.user));
    return data;
  },

  /**
   * Register a new student account.
   */
  async registerStudent(payload: StudentRegisterPayload): Promise<User> {
    const response = await apiClient.post<User>('/auth/register/student', payload);
    return response.data;
  },

  /**
   * Revoke refresh token and clear credentials on server and client.
   */
  async logout(): Promise<void> {
    try {
      const refreshToken = await SecureStoreService.getRefreshToken();
      if (refreshToken) {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch {
      // Even if network or server revocation fails, client tokens must be purged
    } finally {
      await SecureStoreService.clearAllCredentials();
    }
  },

  /**
   * Fetch current authenticated user profile.
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    await SecureStoreService.saveCachedUser(JSON.stringify(response.data));
    return response.data;
  },
};
