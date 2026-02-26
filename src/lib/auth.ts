// Authentication utility functions

import type { AuthTokens, User } from '../types/auth.js';

const ACCESS_TOKEN_KEY = 'sma_access_token';
const REFRESH_TOKEN_KEY = 'sma_refresh_token';
const TOKEN_EXPIRY_KEY = 'sma_token_expiry';
const USER_KEY = 'sma_user';

/**
 * Store authentication tokens in localStorage
 */
export function setTokens(tokens: AuthTokens): void {
  if (typeof window === 'undefined') return;
  
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  if (tokens.expiresAt) {
    localStorage.setItem(TOKEN_EXPIRY_KEY, tokens.expiresAt.toString());
  } else {
    // Calculate expiry from expiresIn (default 24 hours)
    const expiry = Date.now() + (tokens.expiresIn || 86400) * 1000;
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toString());
  }
}

/**
 * Get stored authentication tokens
 */
export function getTokens(): AuthTokens | null {
  if (typeof window === 'undefined') return null;
  
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  const expiresAt = localStorage.getItem(TOKEN_EXPIRY_KEY);
  
  if (!accessToken || !refreshToken || !expiresAt) {
    return null;
  }
  
  return {
    accessToken,
    refreshToken,
    expiresIn: 0,
    expiresAt: parseInt(expiresAt, 10),
  };
}

/**
 * Clear all authentication tokens
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Store user data
 */
export function setUser(user: User): void {
  if (typeof window === 'undefined') return;
  
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get stored user data
 */
export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;
  
  try {
    return JSON.parse(userJson) as User;
  } catch {
    return null;
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const tokens = getTokens();
  if (!tokens) return false;
  
  // Check if token is expired (with 5 minute buffer)
  const now = Date.now();
  const buffer = 5 * 60 * 1000; // 5 minutes
  
  return (tokens.expiresAt || 0) > now + buffer;
}

/**
 * Get the access token for API requests
 */
export function getAccessToken(): string | null {
  const tokens = getTokens();
  return tokens?.accessToken ?? null;
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 * - At least 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 */
export function isValidPassword(password: string): boolean {
  if (password.length < 8) return false;
  if (!/[A-Z]/.test(password)) return false;
  if (!/[a-z]/.test(password)) return false;
  if (!/[0-9]/.test(password)) return false;
  return true;
}

/**
 * Get password validation error message
 */
export function getPasswordError(password: string): string | null {
  if (password.length < 8) {
    return 'Password must be at least 8 characters long';
  }
  if (!/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter';
  }
  if (!/[a-z]/.test(password)) {
    return 'Password must contain at least one lowercase letter';
  }
  if (!/[0-9]/.test(password)) {
    return 'Password must contain at least one number';
  }
  return null;
}
