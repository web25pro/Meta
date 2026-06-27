'use client';

import { useQuery } from 'react-query';
import { Clock } from 'lucide-react';
import { Button, PPAmount, Skeleton, EmptyState } from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { Task, PaginatedResponse } from '@/types';
import { format } from 'date-fns';

export default function QuestsPage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Task>>('tasks', async () => {
    const response = await apiClient.get('/tasks/my-tasks');
    return {
      items: response.data.tasks || [],
      total: response.data.total || 0,
      page: response.data.page || 1,
      page_size: response.data.page_size || 20,
    };
  });

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Quests</h1>
        <p className="mt-1 text-body text-ink-muted">
          Complete verified actions to earn Panda Points.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-lg">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="space-y-lg">
          {data.items.map((task) => (
            <QuestRow key={task.id} task={task} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No quests assigned yet"
          description="New quests appear here as they go live. Check back soon to start earning."
        />
      )}
    </div>
  );
}

function QuestRow({ task }: { task: Task }) {
  const isOverdue = new Date(task.deadline) < new Date();

  return (
    <div className="overflow-hidden rounded-card border border-line border-l-4 border-l-brand-cobalt bg-bg-primary p-lg shadow-card transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-md">
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-h2 text-ink-primary">{task.title}</h3>
          <p className="mt-1 text-body text-ink-muted">{task.description}</p>
        </div>
        <PPAmount value={task.point_value} size="sm" className="shrink-0" />
      </div>

      <div className="mt-lg flex flex-wrap items-center justify-between gap-md">
        <div className="flex items-center gap-md text-label text-ink-muted">
          <span className="flex items-center gap-sm">
            <Clock className="h-4 w-4" />
            Due {format(new Date(task.deadline), 'MMM d, yyyy')}
          </span>
          {isOverdue && (
            <span className="rounded-pill bg-danger/10 px-sm py-[2px] font-medium text-danger">
              Overdue
            </span>
          )}
        </div>
        <Button size="sm">Submit Quest</Button>
      </div>
    </div>
  );
}
