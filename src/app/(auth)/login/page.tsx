"use client";

import { LoginForm } from '@/components/auth/login-form';
import { Sparkles } from 'lucide-react';

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--surface)] p-4">
      <div className="w-full max-w-md">
        {/* Logo and header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-xl bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] mb-4">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text)]">
            Welcome back
          </h1>
          <p className="mt-2 text-[var(--text-muted)]">
            Sign in to your Social Media AI Panel account
          </p>
        </div>

        {/* Login form */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6 sm:p-8 shadow-sm">
          <LoginForm />
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
          By signing in, you agree to our{' '}
          <a href="#" className="text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors cursor-pointer">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="#" className="text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors cursor-pointer">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
}
