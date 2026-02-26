// Theme utility functions for dark mode

const THEME_KEY = 'sma_theme';

export type Theme = 'light' | 'dark' | 'system';

/**
 * Get the current theme from localStorage
 */
export function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'system';
  
  const stored = localStorage.getItem(THEME_KEY) as Theme | null;
  if (stored && ['light', 'dark', 'system'].includes(stored)) {
    return stored;
  }
  return 'system';
}

/**
 * Store theme preference
 */
export function setStoredTheme(theme: Theme): void {
  if (typeof window === 'undefined') return;
  
  localStorage.setItem(THEME_KEY, theme);
}

/**
 * Apply theme to document
 */
export function applyTheme(theme: Theme): void {
  if (typeof window === 'undefined') return;
  
  const root = document.documentElement;
  
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  } else if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

/**
 * Initialize theme on page load
 */
export function initTheme(): void {
  if (typeof window === 'undefined') return;
  
  const theme = getStoredTheme();
  applyTheme(theme);
  
  // Listen for system theme changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  mediaQuery.addEventListener('change', () => {
    const currentTheme = getStoredTheme();
    if (currentTheme === 'system') {
      applyTheme('system');
    }
  });
}

/**
 * Toggle between light and dark mode
 */
export function toggleTheme(): Theme {
  const currentTheme = getStoredTheme();
  const root = document.documentElement;
  
  let newTheme: Theme;
  if (currentTheme === 'dark' || (currentTheme === 'system' && root.classList.contains('dark'))) {
    newTheme = 'light';
  } else {
    newTheme = 'dark';
  }
  
  setStoredTheme(newTheme);
  applyTheme(newTheme);
  
  return newTheme;
}
