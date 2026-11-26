import axios from 'axios';
import { apiClient } from '../api/client';
import { AuthApi } from '../api/auth';
import { SecureStoreService } from '../services/secureStore';

jest.mock('../services/secureStore', () => ({
  SecureStoreService: {
    saveTokens: jest.fn(),
    getAccessToken: jest.fn(),
    getRefreshToken: jest.fn(),
    saveCachedUser: jest.fn(),
    getCachedUser: jest.fn(),
    clearAllCredentials: jest.fn(),
  },
}));

jest.mock('axios', () => {
  const mAxiosInstance = {
    defaults: { baseURL: '', headers: {} },
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    post: jest.fn(),
    get: jest.fn(),
  };
  const mAxios: any = jest.fn(() => mAxiosInstance);
  mAxios.create = jest.fn(() => mAxiosInstance);
  mAxios.post = jest.fn();
  mAxios.get = jest.fn();
  return mAxios;
});

describe('AuthApi & Contracts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('login sends payload to /auth/login and securely persists tokens', async () => {
    const mockUser = {
      id: 'u1',
      email: 'student@example.com',
      full_name: 'Test Student',
      is_active: true,
      is_email_verified: true,
      created_at: '2026-11-26T00:00:00Z',
      roles: [{ id: 'r1', name: 'STUDENT' }],
    };

    const mockResponse = {
      data: {
        access_token: 'acc_token_999',
        refresh_token: 'ref_token_888',
        token_type: 'bearer',
        expires_in: 900,
        user: mockUser,
      },
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    const result = await AuthApi.login({
      email: 'student@example.com',
      password: 'password123',
    });

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
      email: 'student@example.com',
      password: 'password123',
    });

    expect(SecureStoreService.saveTokens).toHaveBeenCalledWith('acc_token_999', 'ref_token_888');
    expect(SecureStoreService.saveCachedUser).toHaveBeenCalledWith(JSON.stringify(mockUser));
    expect(result.access_token).toBe('acc_token_999');
  });

  it('logout attempts server revocation and purges local credentials', async () => {
    (SecureStoreService.getRefreshToken as jest.Mock).mockResolvedValue('ref_token_to_revoke');
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { status: 'ok' } });

    await AuthApi.logout();

    expect(apiClient.post).toHaveBeenCalledWith('/auth/logout', {
      refresh_token: 'ref_token_to_revoke',
    });
    expect(SecureStoreService.clearAllCredentials).toHaveBeenCalled();
  });
});
