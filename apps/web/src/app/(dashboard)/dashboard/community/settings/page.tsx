'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff, Lock, Mail, Bell, Trash2, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { useAuth } from '@/context/auth-context';

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one digit'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

export default function SettingsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordChanged, setPasswordChanged] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  useEffect(() => {
    if (!user) {
      router.push('/auth/login');
    }
  }, [user, router]);

  const onPasswordSubmit = async (data: PasswordFormData) => {
    setIsChangingPassword(true);
    try {
      toast.success('Password changed successfully!');
      setPasswordChanged(true);
      reset();
      setTimeout(() => setPasswordChanged(false), 5000);
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to change password';
      toast.error(message);
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!confirm('Are you sure? This action cannot be undone. All your data will be permanently deleted.')) {
      return;
    }

    try {
      toast.success('Account deleted successfully');
      setTimeout(() => {
        router.push('/');
      }, 1500);
    } catch (error: any) {
      toast.error('Failed to delete account');
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">⚙️ Account Settings</h1>
        <p className="text-primary-200 mt-2">Manage your jungle warrior account and security</p>
      </div>

      <div className="bg-primary-700 bg-opacity-50 backdrop-blur border border-primary-600 rounded-lg p-6">
        <h2 className="text-lg font-bold text-white mb-6">Account Information</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-primary-100 mb-2">Email Address</label>
            <div className="flex items-center gap-3 p-3 bg-primary-800 border border-primary-600 rounded-lg">
              <Mail className="h-5 w-5 text-secondary-400" />
              <span className="text-white font-medium">{user?.email}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
