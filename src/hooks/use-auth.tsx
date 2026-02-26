"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User, LoginCredentials, RegisterCredentials, AuthResponse } from '../types/auth';
import { 
  setTokens, 
  clearTokens, 
  setUser, 
  getUser, 
  isAuthenticated as checkIsAuthenticated,
} from '../lib/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Mock API call for authentication
// In production, this would call the actual backend API
async function mockAuthApi(endpoint: string, data: unknown): Promise<AuthResponse> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800));
  
  if (endpoint === '/api/auth/login') {
    const { email } = data as LoginCredentials;
    
    // Mock validation
    if (email === 'test@example.com') {
      throw new Error('Invalid credentials');
    }
    
    return {
      user: {
        id: 'user-001',
        email,
        name: email.split('@')[0],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      tokens: {
        accessToken: 'mock-access-token-' + Math.random().toString(36).substring(7),
        refreshToken: 'mock-refresh-token-' + Math.random().toString(36).substring(7),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
      },
    };
  }
  
  if (endpoint === '/api/auth/register') {
    const { email, name } = data as RegisterCredentials;
    
    return {
      user: {
        id: 'user-' + Math.random().toString(36).substring(7),
        email,
        name,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      tokens: {
        accessToken: 'mock-access-token-' + Math.random().toString(36).substring(7),
        refreshToken: 'mock-refresh-token-' + Math.random().toString(36).substring(7),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000,
      },
    };
  }
  
  throw new Error('Unknown endpoint');
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from storage
  useEffect(() => {
    const initAuth = () => {
      const storedUser = getUser();
      const isAuth = checkIsAuthenticated();
      
      if (storedUser && isAuth) {
        setUserState(storedUser);
      } else if (!isAuth) {
        clearTokens();
      }
      
      setIsLoading(false);
    };
    
    initAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    
    try {
      const response = await mockAuthApi('/api/auth/login', credentials);
      
      setTokens(response.tokens);
      setUser(response.user);
      setUserState(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials) => {
    setIsLoading(true);
    
    try {
      const response = await mockAuthApi('/api/auth/register', credentials);
      
      setTokens(response.tokens);
      setUser(response.user);
      setUserState(response.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUserState(null);
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
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
