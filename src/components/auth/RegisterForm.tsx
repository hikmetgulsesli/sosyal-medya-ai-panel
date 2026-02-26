"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { Eye, EyeOff, Loader2 } from "lucide-react";

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

export function RegisterForm() {
  const router = useRouter();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [acceptTerms, setAcceptTerms] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    } else if (name.length < 2) {
      newErrors.name = "Name must be at least 2 characters";
    }

    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
      newErrors.password = "Password must contain uppercase, lowercase, and number";
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    if (!acceptTerms) {
      setErrors({ general: "Please accept the terms and conditions" });
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      await register({ name, email, password, confirmPassword });
      router.push("/dashboard");
    } catch (err) {
      setErrors({
        general: err instanceof Error ? err.message : "Registration failed. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrength = (pwd: string): { strength: number; label: string } => {
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (/[a-z]/.test(pwd)) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;

    const labels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"];
    return { strength, label: labels[strength] };
  };

  const passwordStrength = getPasswordStrength(password);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errors.general && (
        <div className="rounded-lg border border-[var(--destructive)]/20 bg-[var(--destructive)]/10 p-3 text-sm text-[var(--destructive)]">
          {errors.general}
        </div>
      )}

      <div>
        <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-[var(--text)]">
          Full Name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="John Doe"
          autoComplete="name"
          className={`w-full rounded-lg border bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 ${
            errors.name
              ? "border-[var(--destructive)] focus:ring-[var(--destructive)]/20"
              : "border-[var(--border)] focus:border-[var(--primary)] focus:ring-[var(--primary)]/20"
          }`}
        />
        {errors.name && (
          <p className="mt-1 text-xs text-[var(--destructive)]">{errors.name}</p>
        )}
      </div>

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
            placeholder="Create a strong password"
            autoComplete="new-password"
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
        {password && (
          <div className="mt-2">
            <div className="flex h-1.5 gap-1">
              {[1, 2, 3, 4, 5].map((level) => (
                <div
                  key={level}
                  className={`h-full flex-1 rounded-full transition-colors ${
                    level <= passwordStrength.strength
                      ? passwordStrength.strength >= 4
                        ? "bg-[var(--success)]"
                        : passwordStrength.strength >= 3
                        ? "bg-[var(--warning)]"
                        : "bg-[var(--error)]"
                      : "bg-[var(--border)]"
                  }`}
                />
              ))}
            </div>
            <p className={`mt-1 text-xs ${
              passwordStrength.strength >= 4
                ? "text-[var(--success)]"
                : passwordStrength.strength >= 3
                ? "text-[var(--warning)]"
                : "text-[var(--error)]"
            }`}>
              {passwordStrength.label}
            </p>
          </div>
        )}
        {errors.password && (
          <p className="mt-1 text-xs text-[var(--destructive)]">{errors.password}</p>
        )}
      </div>

      <div>
        <label htmlFor="confirmPassword" className="mb-1.5 block text-sm font-medium text-[var(--text)]">
          Confirm Password
        </label>
        <input
          id="confirmPassword"
          type={showPassword ? "text" : "password"}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Confirm your password"
          autoComplete="new-password"
          className={`w-full rounded-lg border bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 ${
            errors.confirmPassword
              ? "border-[var(--destructive)] focus:ring-[var(--destructive)]/20"
              : "border-[var(--border)] focus:border-[var(--primary)] focus:ring-[var(--primary)]/20"
          }`}
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-xs text-[var(--destructive)]">{errors.confirmPassword}</p>
        )}
      </div>

      <div className="flex items-start gap-2">
        <input
          id="terms"
          type="checkbox"
          checked={acceptTerms}
          onChange={(e) => setAcceptTerms(e.target.checked)}
          className="mt-0.5 h-4 w-4 rounded border-[var(--border)] text-[var(--primary)] focus:ring-[var(--primary)]"
        />
        <label htmlFor="terms" className="text-sm text-[var(--text-muted)]">
          I agree to the{" "}
          <Link href="/terms" className="text-[var(--primary)] hover:text-[var(--primary-hover)]">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-[var(--primary)] hover:text-[var(--primary-hover)]">
            Privacy Policy
          </Link>
        </label>
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
            Creating account...
          </>
        ) : (
          "Create account"
        )}
      </button>
    </form>
  );
}
