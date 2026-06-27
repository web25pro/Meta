'use client';

import { useQuery } from 'react-query';
import { Bell, Calendar, Users } from 'lucide-react';
import { Card, Skeleton, EmptyState } from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { Announcement, PaginatedResponse } from '@/types';
import { format } from 'date-fns';

export default function AnnouncementsPage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Announcement>>(
    'announcements',
    async () => (await apiClient.get('/announcements')).data,
  );

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Announcements</h1>
        <p className="mt-1 text-body text-ink-muted">
          The latest from the Meta-Jungle team.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-lg">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="space-y-lg">
          {data.items.map((a) => (
            <AnnouncementCard key={a.id} announcement={a} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No announcements"
          description="Check back later for news, drops and campaign updates."
          icon={<Bell className="h-12 w-12 text-brand-cobalt" />}
        />
      )}
    </div>
  );
}

function AnnouncementCard({ announcement }: { announcement: Announcement }) {
  return (
    <Card className="flex items-start gap-md border-l-4 border-l-brand-cobalt">
      <div className="shrink-0 rounded-full bg-brand-ice p-3">
        <Bell className="h-6 w-6 text-brand-cobalt" />
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="font-display text-h2 text-ink-primary">{announcement.title}</h3>
        <p className="mt-sm whitespace-pre-wrap text-body text-ink-primary">
          {announcement.content}
        </p>
        <div className="mt-md flex flex-wrap items-center gap-md text-label text-ink-muted">
          <span className="flex items-center gap-sm">
            <Calendar className="h-4 w-4" />
            {format(new Date(announcement.created_at), 'MMM d, yyyy h:mm a')}
          </span>
          <span className="flex items-center gap-sm">
            <Users className="h-4 w-4" /> {announcement.target_group}
          </span>
        </div>
      </div>
    </Card>
  );
}
