import { LoginForm } from "@/components/auth/LoginForm";
import { Sparkles } from "lucide-react";
import Link from "next/link";

export const metadata = {
  title: "Sign In | Social Media AI Panel",
  description: "Sign in to your Social Media AI Panel account",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--primary)]">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-[var(--text)]">SMPanel</h1>
              <p className="text-sm text-[var(--text-muted)]">AI Powered Social Media</p>
            </div>
          </Link>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-lg sm:p-8">
          <div className="mb-6 text-center">
            <h2 className="text-2xl font-bold text-[var(--text)]">Welcome back</h2>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              Sign in to your account to continue
            </p>
          </div>

          <LoginForm />

          <div className="mt-6 text-center">
            <p className="text-sm text-[var(--text-muted)]">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="font-medium text-[var(--primary)] hover:text-[var(--primary-hover)]"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-[var(--text-muted)]">
          By signing in, you agree to our{" "}
          <Link href="/terms" className="underline hover:text-[var(--text)]">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="underline hover:text-[var(--text)]">
            Privacy Policy
          </Link>
        </p>
      </div>
    </div>
  );
}
