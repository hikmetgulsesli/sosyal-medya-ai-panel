"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import type {
  User,
  LoginCredentials,
  RegisterCredentials,
  AuthContextType,
  AuthResponse,
  AuthTokens,
} from "@/types/auth";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "smp_auth_tokens";
const USER_KEY = "smp_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for stored auth on mount
    const storedUser = localStorage.getItem(USER_KEY);
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem(USER_KEY);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Login failed");
      }

      const data: AuthResponse = await response.json();
      
      setUser(data.user);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data.tokens));
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Registration failed");
      }

      const data: AuthResponse = await response.json();
      
      setUser(data.user);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data.tokens));
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (): void => {
    setUser(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(STORAGE_KEY);
    
    // Call logout endpoint to invalidate server-side session
    fetch("/api/auth/logout", { method: "POST" }).catch(() => {
      // Silent fail - client-side cleanup is what matters
    });
  };

  const getToken = (): string | null => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    try {
      const tokens: AuthTokens = JSON.parse(stored);
      return tokens.accessToken;
    } catch {
      return null;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    getToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
