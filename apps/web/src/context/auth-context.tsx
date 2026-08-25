'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import apiClient, { clearTokens, getAccessToken } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  email_verified?: boolean;
  is_banned?: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  refreshUser: () => Promise<User | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async (): Promise<User | null> => {
    if (!getAccessToken()) {
      setUser(null);
      return null;
    }

    const { data: userData } = await apiClient.get('/users/me');
    const nextUser: User = {
      id: userData.id,
      email: userData.email,
      username: userData.username,
      email_verified: userData.email_verified,
      is_banned: userData.is_active === false,
    };
    setUser(nextUser);
    localStorage.setItem('user', JSON.stringify(userData));
    return nextUser;
  }, []);

  useEffect(() => {
    // Check if user is logged in by verifying token with the backend
    const checkAuth = async () => {
      try {
        await refreshUser();
      } catch (error) {
        console.error('Auth check failed:', error);
        clearTokens();
        localStorage.removeItem('user');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [refreshUser]);

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    router.push('/auth/login');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, refreshUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
