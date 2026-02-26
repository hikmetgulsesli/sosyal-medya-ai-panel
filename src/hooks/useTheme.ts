"use client";

import { useState, useSyncExternalStore, useCallback } from "react";

const THEME_KEY = "smp_theme";

type Theme = "light" | "dark";

function getServerSnapshot(): boolean {
  return false;
}

function getClientSnapshot(): boolean {
  return true;
}

function subscribe(): () => void {
  return () => {};
}

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  
  const stored = localStorage.getItem(THEME_KEY) as Theme | null;
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  
  return stored || (prefersDark ? "dark" : "light");
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);
  const mounted = useSyncExternalStore(subscribe, getClientSnapshot, getServerSnapshot);

  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem(THEME_KEY, newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  }, []);

  const toggleTheme = useCallback(() => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
  }, [theme, setTheme]);

  return { theme, toggleTheme, setTheme, mounted };
}
