'use client';

import { useQuery } from 'react-query';
import { Plus, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import apiClient from '@/lib/api';
import { Task, PaginatedResponse } from '@/types';
import { format } from 'date-fns';

export default function TasksPage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Task>>('tasks', async () => {
    const response = await apiClient.get('/tasks/my-tasks');
    return {
      items: response.data.tasks || [],
      total: response.data.total || 0,
      page: response.data.page || 1,
      page_size: response.data.page_size || 20,
    };
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Tasks</h1>
          <p className="text-gray-600 mt-1">View and manage your assigned tasks</p>
        </div>
      </div>

      {/* Tasks Grid */}
      <div className="grid gap-6">
        {data?.items.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
        {data?.items.length === 0 && (
          <div className="text-center py-12 bg-white rounded-xl">
            <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks assigned</h3>
            <p className="text-gray-600">You don&apos;t have any tasks assigned yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function TaskCard({ task }: { task: Task }) {
  const isOverdue = new Date(task.deadline) < new Date();

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{task.title}</h3>
          <p className="text-gray-600">{task.description}</p>
        </div>
        <div className="ml-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-100 text-primary-800">
            {task.point_value} PP
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>Due {format(new Date(task.deadline), 'MMM d, yyyy')}</span>
          </div>
          {isOverdue && (
            <span className="text-red-600 font-medium">Overdue</span>
          )}
        </div>
        <button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
          Submit Task
        </button>
      </div>
    </div>
  );
}
