"use client";

import { useState, useCallback, type ChangeEvent, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../hooks/use-auth';
import { isValidEmail, getPasswordError } from '../../lib/auth';
import { cn } from '../../lib/utils';
import { Eye, EyeOff, Mail, Lock, User, Loader2, Check, X } from 'lucide-react';

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

interface PasswordStrength {
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
}

export function RegisterForm() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [touched, setTouched] = useState({
    name: false,
    email: false,
    password: false,
    confirmPassword: false,
  });

  const passwordStrength: PasswordStrength = {
    hasMinLength: formData.password.length >= 8,
    hasUppercase: /[A-Z]/.test(formData.password),
    hasLowercase: /[a-z]/.test(formData.password),
    hasNumber: /[0-9]/.test(formData.password),
  };

  const isPasswordStrong = Object.values(passwordStrength).every(Boolean);

  const validateField = useCallback((name: string, value: string): string | undefined => {
    switch (name) {
      case 'name':
        if (!value.trim()) return 'Name is required';
        if (value.trim().length < 2) return 'Name must be at least 2 characters';
        return undefined;
      case 'email':
        if (!value) return 'Email is required';
        if (!isValidEmail(value)) return 'Please enter a valid email address';
        return undefined;
      case 'password':
        if (!value) return 'Password is required';
        const passwordError = getPasswordError(value);
        if (passwordError) return passwordError;
        return undefined;
      case 'confirmPassword':
        if (!value) return 'Please confirm your password';
        if (value !== formData.password) return 'Passwords do not match';
        return undefined;
      default:
        return undefined;
    }
  }, [formData.password]);

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
    
    const nameError = validateField('name', formData.name);
    if (nameError) newErrors.name = nameError;
    
    const emailError = validateField('email', formData.email);
    if (emailError) newErrors.email = emailError;
    
    const passwordError = validateField('password', formData.password);
    if (passwordError) newErrors.password = passwordError;
    
    const confirmPasswordError = validateField('confirmPassword', formData.confirmPassword);
    if (confirmPasswordError) newErrors.confirmPassword = confirmPasswordError;
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setTouched({ name: true, email: true, password: true, confirmPassword: true });
      return;
    }
    
    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        confirmPassword: formData.confirmPassword,
      });
      
      // Redirect to dashboard on success
      router.push('/dashboard');
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'Registration failed. Please try again.',
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
          htmlFor="name" 
          className="block text-sm font-medium text-[var(--text)]"
        >
          Full name
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <User className="h-5 w-5 text-[var(--text-muted)]" />
          </div>
          <input
            id="name"
            name="name"
            type="text"
            autoComplete="name"
            required
            value={formData.name}
            onChange={handleChange}
            onBlur={handleBlur}
            className={cn(
              "block w-full rounded-lg border bg-[var(--surface-elevated)] pl-10 pr-4 py-2.5 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] transition-colors",
              touched.name && errors.name 
                ? "border-[var(--error)] focus:ring-[var(--error)]" 
                : "border-[var(--border)]"
            )}
            placeholder="John Doe"
          />
        </div>
        {touched.name && errors.name && (
          <p className="text-sm text-[var(--error)]">{errors.name}</p>
        )}
      </div>
      
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
            autoComplete="new-password"
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
            placeholder="Create a password"
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
        
        {/* Password strength indicator */}
        {formData.password && (
          <div className="space-y-2 mt-2">
            <div className="flex gap-1">
              {[1, 2, 3, 4].map((level) => {
                const strength = Object.values(passwordStrength).filter(Boolean).length;
                const isActive = level <= strength;
                return (
                  <div
                    key={level}
                    className={cn(
                      "h-1 flex-1 rounded-full transition-colors",
                      isActive 
                        ? strength <= 2 
                          ? "bg-[var(--error)]" 
                          : strength === 3 
                            ? "bg-[var(--warning)]" 
                            : "bg-[var(--success)]"
                        : "bg-[var(--border)]"
                    )}
                  />
                );
              })}
            </div>
            <ul className="space-y-1 text-xs">
              <PasswordRequirement 
                met={passwordStrength.hasMinLength} 
                label="At least 8 characters" 
              />
              <PasswordRequirement 
                met={passwordStrength.hasUppercase} 
                label="One uppercase letter" 
              />
              <PasswordRequirement 
                met={passwordStrength.hasLowercase} 
                label="One lowercase letter" 
              />
              <PasswordRequirement 
                met={passwordStrength.hasNumber} 
                label="One number" 
              />
            </ul>
          </div>
        )}
        
        {touched.password && errors.password && !formData.password && (
          <p className="text-sm text-[var(--error)]">{errors.password}</p>
        )}
      </div>

      <div className="space-y-2">
        <label 
          htmlFor="confirmPassword" 
          className="block text-sm font-medium text-[var(--text)]"
        >
          Confirm password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock className="h-5 w-5 text-[var(--text-muted)]" />
          </div>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            required
            value={formData.confirmPassword}
            onChange={handleChange}
            onBlur={handleBlur}
            className={cn(
              "block w-full rounded-lg border bg-[var(--surface-elevated)] pl-10 pr-12 py-2.5 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] transition-colors",
              touched.confirmPassword && errors.confirmPassword 
                ? "border-[var(--error)] focus:ring-[var(--error)]" 
                : "border-[var(--border)]"
            )}
            placeholder="Confirm your password"
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
            tabIndex={-1}
          >
            {showConfirmPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        </div>
        {touched.confirmPassword && errors.confirmPassword && (
          <p className="text-sm text-[var(--error)]">{errors.confirmPassword}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading || !isPasswordStrong}
        className="w-full flex items-center justify-center rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating account...
          </>
        ) : (
          'Create account'
        )}
      </button>

      <p className="text-center text-sm text-[var(--text-muted)]">
        Already have an account?{' '}
        <Link 
          href="/login" 
          className="font-medium text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors cursor-pointer"
        >
          Sign in
        </Link>
      </p>
    </form>
  );
}

function PasswordRequirement({ met, label }: { met: boolean; label: string }) {
  return (
    <li className={cn(
      "flex items-center gap-1.5 transition-colors",
      met ? "text-[var(--success)]" : "text-[var(--text-muted)]"
    )}>
      {met ? (
        <Check className="h-3.5 w-3.5" />
      ) : (
        <X className="h-3.5 w-3.5" />
      )}
      <span>{label}</span>
    </li>
  );
}
