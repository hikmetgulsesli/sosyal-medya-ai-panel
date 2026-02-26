"use client";

import { useState, useCallback, type ChangeEvent, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../hooks/use-auth';
import { isValidEmail } from '../../lib/auth';
import { cn } from '../../lib/utils';
import { Eye, EyeOff, Mail, Lock, Loader2 } from 'lucide-react';

interface FormErrors {
  email?: string;
  password?: string;
  general?: string;
}

export function LoginForm() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState({
    email: false,
    password: false,
  });

  const validateField = useCallback((name: string, value: string): string | undefined => {
    switch (name) {
      case 'email':
        if (!value) return 'Email is required';
        if (!isValidEmail(value)) return 'Please enter a valid email address';
        return undefined;
      case 'password':
        if (!value) return 'Password is required';
        return undefined;
      default:
        return undefined;
    }
  }, []);

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  }, [errors]);

  const handleBlur = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    
    const error = validateField(name, value);
    if (error) {
      setErrors(prev => ({ ...prev, [name]: error }));
    }
  }, [validateField]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // Validate all fields
    const newErrors: FormErrors = {};
    
    const emailError = validateField('email', formData.email);
    if (emailError) newErrors.email = emailError;
    
    const passwordError = validateField('password', formData.password);
    if (passwordError) newErrors.password = passwordError;
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setTouched({ email: true, password: true });
      return;
    }
    
    try {
      await login({
        email: formData.email,
        password: formData.password,
      });
      
      // Redirect to dashboard on success
      router.push('/dashboard');
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'Login failed. Please try again.',
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {errors.general && (
        <div className="rounded-lg bg-[var(--error)]/10 border border-[var(--error)]/20 p-4 text-sm text-[var(--error)]">
          {errors.general}
        </div>
      )}
      
      <div className="space-y-2">
        <label 
          htmlFor="email" 
          className="block text-sm font-medium text-[var(--text)]"
        >
          Email address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Mail className="h-5 w-5 text-[var(--text-muted)]" />
          </div>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={formData.email}
            onChange={handleChange}
            onBlur={handleBlur}
            className={cn(
              "block w-full rounded-lg border bg-[var(--surface-elevated)] pl-10 pr-4 py-2.5 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] transition-colors",
              touched.email && errors.email 
                ? "border-[var(--error)] focus:ring-[var(--error)]" 
                : "border-[var(--border)]"
            )}
            placeholder="you@example.com"
          />
        </div>
        {touched.email && errors.email && (
          <p className="text-sm text-[var(--error)]">{errors.email}</p>
        )}
      </div>

      <div className="space-y-2">
        <label 
          htmlFor="password" 
          className="block text-sm font-medium text-[var(--text)]"
        >
          Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock className="h-5 w-5 text-[var(--text-muted)]" />
          </div>
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            required
            value={formData.password}
            onChange={handleChange}
            onBlur={handleBlur}
            className={cn(
              "block w-full rounded-lg border bg-[var(--surface-elevated)] pl-10 pr-12 py-2.5 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] transition-colors",
              touched.password && errors.password 
                ? "border-[var(--error)] focus:ring-[var(--error)]" 
                : "border-[var(--border)]"
            )}
            placeholder="Enter your password"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        </div>
        {touched.password && errors.password && (
          <p className="text-sm text-[var(--error)]">{errors.password}</p>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            id="remember-me"
            name="remember-me"
            type="checkbox"
            className="h-4 w-4 rounded border-[var(--border)] bg-[var(--surface-elevated)] text-[var(--primary)] focus:ring-[var(--primary)] cursor-pointer"
          />
          <label 
            htmlFor="remember-me" 
            className="ml-2 block text-sm text-[var(--text-muted)] cursor-pointer"
          >
            Remember me
          </label>
        </div>
        
        <Link 
          href="/forgot-password" 
          className="text-sm font-medium text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors cursor-pointer"
        >
          Forgot password?
        </Link>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex items-center justify-center rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Signing in...
          </>
        ) : (
          'Sign in'
        )}
      </button>

      <p className="text-center text-sm text-[var(--text-muted)]">
        Don&apos;t have an account?{' '}
        <Link 
          href="/register" 
          className="font-medium text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors cursor-pointer"
        >
          Create one
        </Link>
      </p>
    </form>
  );
}
