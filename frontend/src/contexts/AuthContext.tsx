import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { message } from 'antd';
import type { ReactNode } from 'react';
import type { AuthUser } from '../types';
import { login as loginApi } from '../services/auth';
import { AUTH_TOKEN_STORAGE_KEY, AUTH_USER_STORAGE_KEY } from '../services/api';

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  initializing: boolean;
  authenticating: boolean;
  login: (userId: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const parseStoredUser = (raw: string | null): AuthUser | null => {
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as AuthUser;
    if (parsed && parsed.userId && parsed.role) {
      return parsed;
    }
  } catch (error) {
    console.warn('Failed to parse stored user payload', error);
  }
  return null;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [authenticating, setAuthenticating] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    const storedUser = parseStoredUser(localStorage.getItem(AUTH_USER_STORAGE_KEY));
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    } else {
      localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
      localStorage.removeItem(AUTH_USER_STORAGE_KEY);
    }
    setInitializing(false);
  }, []);

  const login = useCallback(async (userId: string, password: string) => {
    setAuthenticating(true);
    try {
      const response = await loginApi(userId.trim(), password);
      const normalizedUser: AuthUser = {
        userId: response.user.user_id,
        role: response.user.role,
        status: response.user.status,
        createdAt: response.user.created_at,
      };
      localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token);
      localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(normalizedUser));
      setUser(normalizedUser);
      setToken(response.access_token);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '登录失败，请稍后重试';
      message.error(detail);
      throw error;
    } finally {
      setAuthenticating(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    localStorage.removeItem(AUTH_USER_STORAGE_KEY);
    setUser(null);
    setToken(null);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    initializing,
    authenticating,
    login,
    logout,
  }), [user, token, initializing, authenticating, login, logout]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
