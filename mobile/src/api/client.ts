import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { SecureStoreService } from '../services/secureStore';
import { TokenResponse } from './types';

// Android emulator typically accesses host localhost at 10.0.2.2; standard local network or localhost fallback
export const DEFAULT_API_BASE_URL = 'http://10.0.2.2:8000/api/v1';

let activeBaseUrl = DEFAULT_API_BASE_URL;

export function setApiBaseUrl(url: string) {
  activeBaseUrl = url;
  apiClient.defaults.baseURL = activeBaseUrl;
}

export function getApiBaseUrl(): string {
  return activeBaseUrl;
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: DEFAULT_API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Mutex & queue for concurrent 401 handling
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else if (token) {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// Request interceptor: Attach JWT bearer token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Avoid attaching bearer token to login/register/refresh endpoints if not desired
    if (
      !config.url?.includes('/auth/login') &&
      !config.url?.includes('/auth/register') &&
      !config.url?.includes('/auth/refresh')
    ) {
      const accessToken = await SecureStoreService.getAccessToken();
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Single-flight 401 token refresh queue
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If error is not 401 or request has already retried, fail immediately
    if (!error.response || error.response.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Do not attempt refresh on auth endpoints themselves (e.g. login failed with 401)
    if (
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/register')
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Enqueue the pending request until active refresh completes
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((newAccessToken) => {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshToken = await SecureStoreService.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // Execute refresh using raw axios to avoid interceptor loop
      const response = await axios.post<TokenResponse>(
        `${activeBaseUrl}/auth/refresh`,
        { refresh_token: refreshToken },
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 10000,
        }
      );

      const { access_token, refresh_token: new_refresh_token } = response.data;
      await SecureStoreService.saveTokens(access_token, new_refresh_token);

      processQueue(null, access_token);
      originalRequest.headers.Authorization = `Bearer ${access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      // On hard refresh failure, wipe credentials
      await SecureStoreService.clearAllCredentials();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
