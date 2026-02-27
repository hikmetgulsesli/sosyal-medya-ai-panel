"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/hooks/useTheme";
import { User, Mail, Sun, Moon, Save, Key, Plus, Trash2, Eye, EyeOff } from "lucide-react";

interface ApiKeyEntry {
  id: string;
  platform: string;
  key: string;
  addedAt: string;
}

const PLATFORMS = [
  { value: "twitter", label: "Twitter / X" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "instagram", label: "Instagram" },
  { value: "bluesky", label: "Bluesky" },
];

const API_KEYS_STORAGE = "smp_api_keys";

export default function SettingsPage() {
  const { user, getToken } = useAuth();
  const { theme, setTheme, mounted } = useTheme();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKeyEntry[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPlatform, setNewPlatform] = useState("");
  const [newKey, setNewKey] = useState("");
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setEmail(user.email || "");
    }
  }, [user]);

  useEffect(() => {
    const stored = localStorage.getItem(API_KEYS_STORAGE);
    if (stored) {
      try { setApiKeys(JSON.parse(stored)); } catch { /* ignore */ }
    }
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      const token = getToken();
      const res = await fetch("/api/auth/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ full_name: name, email }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error?.message || "Failed to update profile");
      }

      setMessage({ type: "success", text: "Profile updated successfully." });
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Update failed" });
    } finally {
      setSaving(false);
    }
  };

  const handleAddKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlatform || !newKey) return;

    const entry: ApiKeyEntry = {
      id: crypto.randomUUID(),
      platform: newPlatform,
      key: newKey,
      addedAt: new Date().toISOString(),
    };
    const updated = [...apiKeys, entry];
    setApiKeys(updated);
    localStorage.setItem(API_KEYS_STORAGE, JSON.stringify(updated));
    setNewPlatform("");
    setNewKey("");
    setShowAddForm(false);
  };

  const handleDeleteKey = (id: string) => {
    const updated = apiKeys.filter((k) => k.id !== id);
    setApiKeys(updated);
    localStorage.setItem(API_KEYS_STORAGE, JSON.stringify(updated));
    setVisibleKeys((prev) => { const next = new Set(prev); next.delete(id); return next; });
  };

  const toggleKeyVisibility = (id: string) => {
    setVisibleKeys((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const maskKey = (key: string) => key.slice(0, 6) + "..." + key.slice(-4);

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          <div>
            <h1 className="text-3xl font-bold text-[var(--text)]">Settings</h1>
            <p className="mt-1 text-[var(--text-muted)]">Manage your account preferences.</p>
          </div>

          {message && (
            <div
              className={`rounded-lg border px-4 py-3 text-sm ${
                message.type === "success"
                  ? "border-[var(--success)]/30 bg-[var(--success)]/10 text-[var(--success)]"
                  : "border-[var(--destructive)]/30 bg-[var(--destructive)]/10 text-[var(--destructive)]"
              }`}
            >
              {message.text}
            </div>
          )}

          {/* Profile */}
          <form onSubmit={handleSaveProfile} className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Profile</h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Your account information.</p>
            <div className="mt-6 space-y-4">
              <div>
                <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-[var(--text)]">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                  <input id="name" type="text" value={name} onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] py-2.5 pl-10 pr-4 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
                    placeholder="Your name" />
                </div>
              </div>
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-[var(--text)]">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                  <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] py-2.5 pl-10 pr-4 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
                    placeholder="you@example.com" />
                </div>
              </div>
            </div>
            <div className="mt-6">
              <button type="submit" disabled={saving}
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 disabled:opacity-50 cursor-pointer"
                style={{ transitionDuration: "var(--duration-normal)" }}>
                <Save className="h-4 w-4" />
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>

          {/* Appearance */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Appearance</h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">Choose your preferred theme.</p>
            <div className="mt-6 flex gap-4">
              {(["light", "dark"] as const).map((t) => (
                <button key={t} onClick={() => setTheme(t)}
                  className={`flex items-center gap-3 rounded-lg border px-5 py-3 text-sm font-medium transition-colors cursor-pointer ${
                    mounted && theme === t
                      ? "border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--primary)]"
                      : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--primary)]/50"
                  }`}
                  style={{ transitionDuration: "var(--duration-normal)" }}>
                  {t === "light" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                  {t === "light" ? "Light" : "Dark"}
                </button>
              ))}
            </div>
          </div>

          {/* API Keys */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-[var(--text)]">API Keys</h2>
                <p className="mt-1 text-sm text-[var(--text-muted)]">Manage API keys for connected platforms.</p>
              </div>
              {!showAddForm && (
                <button onClick={() => setShowAddForm(true)}
                  className="inline-flex items-center gap-2 rounded-lg bg-[var(--primary)] px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}>
                  <Plus className="h-4 w-4" /> Add Key
                </button>
              )}
            </div>

            {/* Add Form */}
            {showAddForm && (
              <form onSubmit={handleAddKey} className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 space-y-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-[var(--text)]">Platform</label>
                  <select value={newPlatform} onChange={(e) => setNewPlatform(e.target.value)}
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--card)] py-2 px-3 text-sm text-[var(--text)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)] cursor-pointer">
                    <option value="">Select platform...</option>
                    {PLATFORMS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-[var(--text)]">API Key</label>
                  <input type="password" value={newKey} onChange={(e) => setNewKey(e.target.value)}
                    className="w-full rounded-lg border border-[var(--border)] bg-[var(--card)] py-2 px-3 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
                    placeholder="Enter your API key..." />
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={!newPlatform || !newKey}
                    className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50 cursor-pointer">
                    Save
                  </button>
                  <button type="button" onClick={() => { setShowAddForm(false); setNewPlatform(""); setNewKey(""); }}
                    className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2 text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] cursor-pointer">
                    Cancel
                  </button>
                </div>
              </form>
            )}

            {/* Keys List */}
            {apiKeys.length === 0 && !showAddForm ? (
              <div className="mt-6 flex items-center gap-3 rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface)] p-8">
                <Key className="h-6 w-6 text-[var(--text-muted)]" />
                <p className="text-sm text-[var(--text-muted)]">No API keys configured yet. Click &quot;Add Key&quot; to get started.</p>
              </div>
            ) : (
              <div className="mt-4 space-y-2">
                {apiKeys.map((entry) => {
                  const platformLabel = PLATFORMS.find((p) => p.value === entry.platform)?.label || entry.platform;
                  const isVisible = visibleKeys.has(entry.id);
                  return (
                    <div key={entry.id} className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Key className="h-4 w-4 text-[var(--text-muted)]" />
                        <div>
                          <p className="text-sm font-medium text-[var(--text)]">{platformLabel}</p>
                          <p className="font-mono text-xs text-[var(--text-muted)]">
                            {isVisible ? entry.key : maskKey(entry.key)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => toggleKeyVisibility(entry.id)}
                          className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
                          aria-label={isVisible ? "Hide key" : "Show key"}>
                          {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                        <button onClick={() => handleDeleteKey(entry.id)}
                          className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--destructive)]/10 hover:text-[var(--destructive)] cursor-pointer"
                          aria-label="Delete key">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
