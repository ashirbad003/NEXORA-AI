import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { User, LoginPayload, StudentRegisterPayload } from '../api/types';
import { AuthApi } from '../api/auth';
import { SecureStoreService } from '../services/secureStore';
import { BiometricService, BiometricCapability } from '../services/biometrics';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isLocked: boolean;
  isBiometricEnrolled: boolean;
  biometricCapability: BiometricCapability | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: StudentRegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  unlockWithBiometrics: () => Promise<boolean>;
  toggleBiometrics: (enabled: boolean) => Promise<boolean>;
  lockSession: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLocked, setIsLocked] = useState<boolean>(false);
  const [isBiometricEnrolled, setIsBiometricEnrolled] = useState<boolean>(false);
  const [biometricCapability, setBiometricCapability] = useState<BiometricCapability | null>(null);
  const appState = useRef<AppStateStatus>(AppState.currentState);

  // AppState listener for background-to-foreground re-lock
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      if (
        appState.current.match(/inactive|background/) &&
        nextAppState === 'active'
      ) {
        // App returned to foreground: if user is authenticated and biometrics enabled, enforce lock
        if (user && isBiometricEnrolled) {
          setIsLocked(true);
        }
      }
      appState.current = nextAppState;
    });

    return () => {
      subscription.remove();
    };
  }, [user, isBiometricEnrolled]);

  // Initialize session state on app launch
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const capability = await BiometricService.checkCapabilities();
        setBiometricCapability(capability);

        const bioEnabled = await SecureStoreService.isBiometricEnabled();
        setIsBiometricEnrolled(bioEnabled && capability.isEnrolled);

        const refreshToken = await SecureStoreService.getRefreshToken();
        if (refreshToken) {
          // Attempt restoring cached user or fetching fresh profile
          const cached = await SecureStoreService.getCachedUser();
          if (cached) {
            try {
              setUser(JSON.parse(cached));
            } catch {
              // Ignore invalid cache JSON
            }
          }

          // If biometric lock is enabled on this device, lock the UI upon cold start
          if (bioEnabled && capability.isEnrolled) {
            setIsLocked(true);
          }

          // Quietly verify / refresh profile
          try {
            const freshUser = await AuthApi.getMe();
            setUser(freshUser);
          } catch {
            // Handled by axios interceptor or offline cache
          }
        }
      } catch {
        // Initialization failure defaults to unauthenticated
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (payload: LoginPayload) => {
    setIsLoading(true);
    try {
      const response = await AuthApi.login(payload);
      setUser(response.user);
      setIsLocked(false);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: StudentRegisterPayload) => {
    setIsLoading(true);
    try {
      await AuthApi.registerStudent(payload);
      // Automatically log in after registration
      const loginResp = await AuthApi.login({
        email: payload.email,
        password: payload.password,
      });
      setUser(loginResp.user);
      setIsLocked(false);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await AuthApi.logout();
    } finally {
      setUser(null);
      setIsLocked(false);
      setIsLoading(false);
    }
  };

  const unlockWithBiometrics = async (): Promise<boolean> => {
    const success = await BiometricService.authenticate('Unlock NEXORA AI');
    if (success) {
      setIsLocked(false);
    }
    return success;
  };

  const toggleBiometrics = async (enabled: boolean): Promise<boolean> => {
    if (enabled) {
      const capability = await BiometricService.checkCapabilities();
      if (!capability.hasHardware || !capability.isEnrolled) {
        return false;
      }
      const verified = await BiometricService.authenticate('Authorize biometric unlock for NEXORA AI');
      if (!verified) return false;

      await SecureStoreService.setBiometricEnabled(true);
      setIsBiometricEnrolled(true);
      return true;
    } else {
      await SecureStoreService.setBiometricEnabled(false);
      setIsBiometricEnrolled(false);
      return true;
    }
  };

  const lockSession = () => {
    if (isBiometricEnrolled) {
      setIsLocked(true);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        isLocked,
        isBiometricEnrolled,
        biometricCapability,
        login,
        register,
        logout,
        unlockWithBiometrics,
        toggleBiometrics,
        lockSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
