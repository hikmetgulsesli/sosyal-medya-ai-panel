"use client";

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../../hooks/use-auth';
import { useTheme } from '../../hooks/use-theme';
import { cn } from '../../lib/utils';
import {
  LayoutDashboard,
  Sparkles,
  Calendar,
  BarChart3,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  Sun,
  Moon,
  Monitor,
  ChevronDown,
} from 'lucide-react';

const navItems = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Content Generator', href: '/dashboard/content', icon: Sparkles },
  { label: 'Scheduler', href: '/dashboard/scheduler', icon: Calendar },
  { label: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { label: 'Competitors', href: '/dashboard/competitors', icon: Users },
];

const bottomNavItems = [
  { label: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, setTheme, isDark } = useTheme();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isThemeMenuOpen, setIsThemeMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
  };

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)] text-[var(--text)] hover:bg-[var(--secondary)] transition-colors cursor-pointer"
        aria-label="Toggle menu"
      >
        {isMobileMenuOpen ? (
          <X className="h-5 w-5" />
        ) : (
          <Menu className="h-5 w-5" />
        )}
      </button>

      {/* Mobile overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-40 h-screen w-64 bg-[var(--surface-elevated)] border-r border-[var(--border)] flex flex-col transition-transform duration-300 lg:translate-x-0",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-[var(--border)]">
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold text-[var(--text)] text-lg">
              AI Panel
            </span>
          </Link>
        </div>

        {/* Main navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
              
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer",
                      isActive
                        ? "bg-[var(--primary)]/10 text-[var(--primary)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--secondary)]"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom section */}
        <div className="border-t border-[var(--border)] p-3 space-y-1">
          {/* Theme toggle */}
          <div className="relative">
            <button
              onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--secondary)] transition-colors cursor-pointer"
            >
              <span className="flex items-center gap-3">
                {isDark ? (
                  <Moon className="h-5 w-5" />
                ) : (
                  <Sun className="h-5 w-5" />
                )}
                Theme
              </span>
              <ChevronDown className={cn(
                "h-4 w-4 transition-transform",
                isThemeMenuOpen && "rotate-180"
              )} />
            </button>
            
            {isThemeMenuOpen && (
              <div className="absolute bottom-full left-0 right-0 mb-1 p-1 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)] shadow-lg">
                <button
                  onClick={() => {
                    setTheme('light');
                    setIsThemeMenuOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors cursor-pointer",
                    theme === 'light'
                      ? "bg-[var(--primary)]/10 text-[var(--primary)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--secondary)]"
                  )}
                >
                  <Sun className="h-4 w-4" />
                  Light
                </button>
                <button
                  onClick={() => {
                    setTheme('dark');
                    setIsThemeMenuOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors cursor-pointer",
                    theme === 'dark'
                      ? "bg-[var(--primary)]/10 text-[var(--primary)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--secondary)]"
                  )}
                >
                  <Moon className="h-4 w-4" />
                  Dark
                </button>
                <button
                  onClick={() => {
                    setTheme('system');
                    setIsThemeMenuOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors cursor-pointer",
                    theme === 'system'
                      ? "bg-[var(--primary)]/10 text-[var(--primary)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--secondary)]"
                  )}
                >
                  <Monitor className="h-4 w-4" />
                  System
                </button>
              </div>
            )}
          </div>

          {/* Settings */}
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer",
                  isActive
                    ? "bg-[var(--primary)]/10 text-[var(--primary)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--secondary)]"
                )}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[var(--text-muted)] hover:text-[var(--error)] hover:bg-[var(--error)]/10 transition-colors cursor-pointer"
          >
            <LogOut className="h-5 w-5" />
            Log out
          </button>

          {/* User info */}
          {user && (
            <div className="mt-3 pt-3 border-t border-[var(--border)] px-3">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-[var(--primary)]/10 flex items-center justify-center">
                  <span className="text-sm font-medium text-[var(--primary)]">
                    {user.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text)] truncate">
                    {user.name}
                  </p>
                  <p className="text-xs text-[var(--text-muted)] truncate">
                    {user.email}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
