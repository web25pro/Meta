import apiClient from '@/lib/api';
import { Task, TaskCreate, PaginatedResponse } from '@/types';

export const tasksAPI = {
  getMyTasks: async (page = 1, pageSize = 20): Promise<PaginatedResponse<Task>> => {
    const response = await apiClient.get<PaginatedResponse<Task>>('/tasks/my-tasks', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getTaskById: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  createTask: async (task: TaskCreate): Promise<Task> => {
    const response = await apiClient.post<Task>('/tasks', task);
    return response.data;
  },

  updateTask: async (taskId: string, task: Partial<TaskCreate>): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${taskId}`, task);
    return response.data;
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/tasks/${taskId}`);
  },
};
