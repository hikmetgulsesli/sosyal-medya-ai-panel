"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Eye, EyeOff, Loader2 } from "lucide-react";

interface FormErrors {
  email?: string;
  password?: string;
  general?: string;
}

export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    setErrors({});

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err) {
      setErrors({
        general: err instanceof Error ? err.message : "Login failed. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errors.general && (
        <div className="rounded-lg border border-[var(--destructive)]/20 bg-[var(--destructive)]/10 p-3 text-sm text-[var(--destructive)]">
          {errors.general}
        </div>
      )}

      <div>
        <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-[var(--text)]">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          className={`w-full rounded-lg border bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 ${
            errors.email
              ? "border-[var(--destructive)] focus:ring-[var(--destructive)]/20"
              : "border-[var(--border)] focus:border-[var(--primary)] focus:ring-[var(--primary)]/20"
          }`}
        />
        {errors.email && (
          <p className="mt-1 text-xs text-[var(--destructive)]">{errors.email}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-[var(--text)]">
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            className={`w-full rounded-lg border bg-[var(--surface)] px-3 py-2.5 pr-10 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 ${
              errors.password
                ? "border-[var(--destructive)] focus:ring-[var(--destructive)]/20"
                : "border-[var(--border)] focus:border-[var(--primary)] focus:ring-[var(--primary)]/20"
            }`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text)] cursor-pointer"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {errors.password && (
          <p className="mt-1 text-xs text-[var(--destructive)]">{errors.password}</p>
        )}
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-[var(--border)] text-[var(--primary)] focus:ring-[var(--primary)]"
          />
          <span className="text-sm text-[var(--text-muted)]">Remember me</span>
        </label>
        <Link
          href="/forgot-password"
          className="text-sm font-medium text-[var(--primary)] hover:text-[var(--primary-hover)]"
        >
          Forgot password?
        </Link>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        style={{ transitionDuration: "var(--duration-normal)" }}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Signing in...
          </>
        ) : (
          "Sign in"
        )}
      </button>
    </form>
  );
}
