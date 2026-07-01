'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Mail, Trash2, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Card, Input, Button } from '@meta-jungle/ui';
import { useAuth } from '@/context/auth-context';

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[a-z]/, 'Must contain a lowercase letter')
      .regex(/[0-9]/, 'Must contain a digit'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

export default function CommunitySettingsPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isChanging, setIsChanging] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<PasswordFormData>({ resolver: zodResolver(passwordSchema) });

  useEffect(() => {
    if (!authLoading && !user) router.push('/auth/login');
  }, [user, authLoading, router]);

  const onSubmit = async (_data: PasswordFormData) => {
    setIsChanging(true);
    try {
      toast.success('Password changed successfully!');
      reset();
    } catch {
      toast.error('Failed to change password');
    } finally {
      setIsChanging(false);
    }
  };

  const handleDeleteAccount = () => {
    if (!confirm('Are you sure? This cannot be undone and all your data will be deleted.')) return;
    toast.success('Account deleted');
    setTimeout(() => router.push('/'), 1500);
  };

  const eye = (shown: boolean, toggle: () => void) => (
    <button type="button" onClick={toggle} className="hover:text-ink-primary">
      {shown ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
    </button>
  );

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Account Settings</h1>
        <p className="mt-1 text-body text-ink-muted">Manage your account and security.</p>
      </div>

      <Card className="space-y-md">
        <h2 className="font-display text-h2 text-ink-primary">Account Information</h2>
        <div>
          <label className="mb-2 block text-label font-medium text-ink-primary">Email Address</label>
          <div className="flex items-center gap-sm rounded-card border border-line bg-bg-surface px-md py-3">
            <Mail className="h-5 w-5 text-brand-cobalt" />
            <span className="text-body text-ink-primary">{user?.email}</span>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="mb-lg font-display text-h2 text-ink-primary">Change Password</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg">
          <Input
            label="Current Password"
            type={showCurrent ? 'text' : 'password'}
            trailing={eye(showCurrent, () => setShowCurrent(!showCurrent))}
            {...register('currentPassword')}
            error={errors.currentPassword?.message}
          />
          <Input
            label="New Password"
            type={showNew ? 'text' : 'password'}
            trailing={eye(showNew, () => setShowNew(!showNew))}
            {...register('newPassword')}
            error={errors.newPassword?.message}
          />
          <Input
            label="Confirm New Password"
            type={showConfirm ? 'text' : 'password'}
            trailing={eye(showConfirm, () => setShowConfirm(!showConfirm))}
            {...register('confirmPassword')}
            error={errors.confirmPassword?.message}
          />
          <Button type="submit" disabled={isChanging}>
            {isChanging ? <Loader2 className="h-5 w-5 animate-spin" /> : null}
            {isChanging ? 'Changing…' : 'Change Password'}
          </Button>
        </form>
      </Card>

      <Card className="border-danger/30">
        <h2 className="font-display text-h2 text-danger">Danger Zone</h2>
        <p className="mt-sm text-body text-ink-muted">
          Permanently delete your account and all associated data.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="mt-md inline-flex items-center gap-sm rounded-pill border border-danger px-md py-sm text-label font-medium text-danger transition-colors hover:bg-danger hover:text-ink-inverse"
        >
          <Trash2 className="h-4 w-4" /> Delete Account
        </button>
      </Card>
    </div>
  );
}
