'use client';

import { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Lock, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Input, Button, ReputationRings, cn } from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { User } from '@/types';

const profileSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
});

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z.string().min(12, 'Password must be at least 12 characters'),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  });

type ProfileFormData = z.infer<typeof profileSchema>;
type PasswordFormData = z.infer<typeof passwordSchema>;

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'password'>('profile');

  const { data: user, refetch } = useQuery<User>('currentUser', async () =>
    (await apiClient.get('/users/me')).data,
  );

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Settings</h1>
        <p className="mt-1 text-body text-ink-muted">
          Manage your account and security.
        </p>
      </div>

      <div className="flex gap-sm">
        {(['profile', 'password'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'rounded-pill px-md py-sm text-label font-medium capitalize transition-colors',
              activeTab === tab
                ? 'bg-brand-cobalt text-ink-inverse'
                : 'border border-line bg-bg-primary text-ink-muted hover:bg-bg-elevated',
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      <Card>
        {activeTab === 'profile' && user && <ProfileForm user={user} onSuccess={refetch} />}
        {activeTab === 'password' && <PasswordForm />}
      </Card>
    </div>
  );
}

function ProfileForm({ user, onSuccess }: { user: User; onSuccess: () => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: user.name, email: user.email },
  });

  const mutation = useMutation(
    async (data: ProfileFormData) => apiClient.patch('/users/me', data),
    {
      onSuccess: () => {
        toast.success('Profile updated');
        onSuccess();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.error?.message || 'Failed to update profile');
      },
    },
  );

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-lg">
      <div className="flex items-center gap-lg">
        <ReputationRings activity={620} reputation={540} influence={310} size={88} />
        <div>
          <h3 className="font-display text-h2 text-ink-primary">{user.name}</h3>
          <p className="text-label text-brand-cobalt">{user.role}</p>
        </div>
      </div>

      <Input label="Full Name" {...register('name')} error={errors.name?.message} />
      <Input label="Email Address" type="email" {...register('email')} error={errors.email?.message} />

      <Button type="submit" disabled={mutation.isLoading}>
        {mutation.isLoading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" /> Saving…
          </>
        ) : (
          <>
            <Save className="h-5 w-5" /> Save Changes
          </>
        )}
      </Button>
    </form>
  );
}

function PasswordForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordFormData>({ resolver: zodResolver(passwordSchema) });

  const mutation = useMutation(
    async (data: PasswordFormData) =>
      apiClient.post('/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password,
      }),
    {
      onSuccess: () => {
        toast.success('Password changed');
        reset();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.error?.message || 'Failed to change password');
      },
    },
  );

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-lg">
      <Input label="Current Password" type="password" {...register('current_password')} error={errors.current_password?.message} />
      <Input label="New Password" type="password" {...register('new_password')} error={errors.new_password?.message} hint="Must be at least 12 characters" />
      <Input label="Confirm New Password" type="password" {...register('confirm_password')} error={errors.confirm_password?.message} />
      <Button type="submit" disabled={mutation.isLoading}>
        {mutation.isLoading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" /> Changing…
          </>
        ) : (
          <>
            <Lock className="h-5 w-5" /> Change Password
          </>
        )}
      </Button>
    </form>
  );
}
