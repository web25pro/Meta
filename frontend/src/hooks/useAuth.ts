import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { authAPI } from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import { setTokens, clearTokens } from '@/lib/api';
import { LoginRequest } from '@/types';

export function useAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, setUser, logout: logoutStore } = useAuthStore();

  const { data: currentUser, isLoading } = useQuery('currentUser', authAPI.getCurrentUser, {
    enabled: !!user,
    onSuccess: (data) => {
      setUser(data);
    },
    onError: () => {
      logoutStore();
      clearTokens();
    },
  });

  const loginMutation = useMutation(authAPI.login, {
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      queryClient.invalidateQueries('currentUser');
      toast.success('Login successful!');
      router.push('/dashboard');
    },
    onError: (error: any) => {
      const message = error.response?.data?.error?.message || 'Login failed';
      toast.error(message);
    },
  });

  const logoutMutation = useMutation(authAPI.logout, {
    onSuccess: () => {
      logoutStore();
      clearTokens();
      queryClient.clear();
      router.push('/login');
      toast.success('Logged out successfully');
    },
  });

  return {
    user: currentUser || user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isLoading,
  };
}
