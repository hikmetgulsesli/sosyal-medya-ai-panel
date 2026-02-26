"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/hooks/useTheme";
import {
  LayoutDashboard,
  Sparkles,
  Calendar,
  BarChart3,
  Menu,
  X,
  Sun,
  Moon,
  LogOut,
  User,
  Settings,
} from "lucide-react";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Content Generator", href: "/content-generator", icon: Sparkles },
  { label: "Scheduler", href: "/scheduler", icon: Calendar },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, toggleTheme, mounted } = useTheme();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const NavLink = ({ item }: { item: typeof navItems[0] }) => {
    const Icon = item.icon;
    const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

    return (
      <Link
        href={item.href}
        className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors cursor-pointer ${
          isActive
            ? "bg-[var(--primary)] text-white"
            : "text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)]"
        }`}
        style={{ transitionDuration: "var(--duration-normal)" }}
      >
        <Icon className="h-5 w-5" />
        {item.label}
      </Link>
    );
  };

  return (
    <>
      {/* Mobile Header */}
      <header className="fixed left-0 right-0 top-0 z-50 border-b border-[var(--border)] bg-[var(--surface-elevated)] lg:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary)]">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold text-[var(--text)]">SMPanel</span>
          </Link>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-50 h-screen w-64 border-r border-[var(--border)] bg-[var(--surface-elevated)] transition-transform lg:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ transitionDuration: "var(--duration-normal)" }}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center gap-3 border-b border-[var(--border)] px-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)]">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-semibold text-[var(--text)]">SMPanel</span>
              <p className="text-xs text-[var(--text-muted)]">AI Powered</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto px-3 py-4">
            <div className="space-y-1">
              {navItems.map((item) => (
                <NavLink key={item.href} item={item} />
              ))}
            </div>
          </nav>

          {/* Bottom Section */}
          <div className="border-t border-[var(--border)] p-3">
            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="mb-2 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-muted)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
              style={{ transitionDuration: "var(--duration-normal)" }}
            >
              {mounted && theme === "dark" ? (
                <>
                  <Sun className="h-5 w-5" />
                  Light Mode
                </>
              ) : (
                <>
                  <Moon className="h-5 w-5" />
                  Dark Mode
                </>
              )}
            </button>

            {/* User Menu */}
            {user && (
              <div className="space-y-1">
                <Link
                  href="/settings"
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-muted)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <Settings className="h-5 w-5" />
                  Settings
                </Link>
                <button
                  onClick={logout}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[var(--text-muted)] transition-colors hover:bg-[var(--destructive)]/10 hover:text-[var(--destructive)] cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <LogOut className="h-5 w-5" />
                  Logout
                </button>
              </div>
            )}

            {/* User Info */}
            {user && (
              <div className="mt-3 flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--primary)]/10">
                  <User className="h-5 w-5 text-[var(--primary)]" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-[var(--text)]">{user.name}</p>
                  <p className="truncate text-xs text-[var(--text-muted)]">{user.email}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
