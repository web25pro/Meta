'use client';

import { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User as UserIcon, Lock, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api';
import { User } from '@/types';

const profileSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
});

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(12, 'Password must be at least 12 characters'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

type ProfileFormData = z.infer<typeof profileSchema>;
type PasswordFormData = z.infer<typeof passwordSchema>;

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'password'>('profile');

  const { data: user, refetch } = useQuery<User>('currentUser', async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account settings</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-4 px-4 font-medium transition-colors ${
            activeTab === 'profile'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab('password')}
          className={`pb-4 px-4 font-medium transition-colors ${
            activeTab === 'password'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Password
        </button>
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        {activeTab === 'profile' && user && <ProfileForm user={user} onSuccess={refetch} />}
        {activeTab === 'password' && <PasswordForm />}
      </div>
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
    defaultValues: {
      name: user.name,
      email: user.email,
    },
  });

  const mutation = useMutation(
    async (data: ProfileFormData) => {
      await apiClient.patch('/users/me', data);
    },
    {
      onSuccess: () => {
        toast.success('Profile updated successfully');
        onSuccess();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.error?.message || 'Failed to update profile');
      },
    }
  );

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
      <div className="flex items-center space-x-4 mb-6">
        <div className="bg-primary-100 rounded-full p-4">
          <UserIcon className="h-12 w-12 text-primary-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
          <p className="text-sm text-gray-600">{user.role}</p>
        </div>
      </div>

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
          Full Name
        </label>
        <input
          {...register('name')}
          type="text"
          id="name"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
          Email Address
        </label>
        <input
          {...register('email')}
          type="email"
          id="email"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
      </div>

      <div className="flex items-center space-x-4 pt-4">
        <button
          type="submit"
          disabled={mutation.isLoading}
          className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
        >
          {mutation.isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Save className="h-5 w-5" />
              <span>Save Changes</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}

function PasswordForm() {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  const mutation = useMutation(
    async (data: PasswordFormData) => {
      await apiClient.post('/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password,
      });
    },
    {
      onSuccess: () => {
        toast.success('Password changed successfully');
        reset();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.error?.message || 'Failed to change password');
      },
    }
  );

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
      <div className="flex items-center space-x-3 mb-6">
        <Lock className="h-6 w-6 text-gray-600" />
        <h3 className="text-lg font-semibold text-gray-900">Change Password</h3>
      </div>

      <div>
        <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 mb-2">
          Current Password
        </label>
        <input
          {...register('current_password')}
          type="password"
          id="current_password"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {errors.current_password && (
          <p className="mt-1 text-sm text-red-600">{errors.current_password.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
          New Password
        </label>
        <input
          {...register('new_password')}
          type="password"
          id="new_password"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {errors.new_password && (
          <p className="mt-1 text-sm text-red-600">{errors.new_password.message}</p>
        )}
        <p className="mt-1 text-sm text-gray-600">Must be at least 12 characters</p>
      </div>

      <div>
        <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
          Confirm New Password
        </label>
        <input
          {...register('confirm_password')}
          type="password"
          id="confirm_password"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {errors.confirm_password && (
          <p className="mt-1 text-sm text-red-600">{errors.confirm_password.message}</p>
        )}
      </div>

      <div className="flex items-center space-x-4 pt-4">
        <button
          type="submit"
          disabled={mutation.isLoading}
          className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
        >
          {mutation.isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Changing...</span>
            </>
          ) : (
            <>
              <Lock className="h-5 w-5" />
              <span>Change Password</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}
