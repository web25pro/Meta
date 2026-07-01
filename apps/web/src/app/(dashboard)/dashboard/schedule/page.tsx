'use client';

import { useQuery } from 'react-query';
import { Clock, Users } from 'lucide-react';
import { Card, Skeleton, EmptyState, cn } from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { Schedule, PaginatedResponse } from '@/types';
import { format, isFuture, isPast, isToday } from 'date-fns';

export default function SchedulePage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Schedule>>('schedule', async () => {
    const response = await apiClient.get('/schedules');
    return response.data;
  });

  const upcoming = data?.items.filter((e) => isFuture(new Date(e.event_date))) || [];
  const past = data?.items.filter((e) => isPast(new Date(e.event_date))) || [];

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Schedule</h1>
        <p className="mt-1 text-body text-ink-muted">
          Upcoming events, drops and deadlines.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-lg">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <>
          <section className="space-y-md">
            <h2 className="font-display text-h2 text-ink-primary">Upcoming</h2>
            {upcoming.length > 0 ? (
              upcoming.map((e) => <EventCard key={e.id} event={e} />)
            ) : (
              <EmptyState
                title="Nothing scheduled"
                description="New events and drops will appear here."
              />
            )}
          </section>

          {past.length > 0 && (
            <section className="space-y-md">
              <h2 className="font-display text-h2 text-ink-primary">Past</h2>
              {past.map((e) => (
                <EventCard key={e.id} event={e} isPast />
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}

function EventCard({ event, isPast = false }: { event: Schedule; isPast?: boolean }) {
  const date = new Date(event.event_date);
  return (
    <Card className={cn('flex items-start gap-lg', isPast && 'opacity-60')}>
      {/* Date chip */}
      <div className="flex w-16 shrink-0 flex-col items-center rounded-card bg-brand-ice py-sm">
        <span className="font-display text-h1 text-brand-cobalt">{format(date, 'd')}</span>
        <span className="text-label uppercase text-brand-cobalt">{format(date, 'MMM')}</span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-sm">
          <h3 className="font-display text-h2 text-ink-primary">{event.title}</h3>
          {isToday(date) && (
            <span className="rounded-pill bg-brand-cobalt px-sm py-[2px] text-label font-medium text-ink-inverse">
              Today
            </span>
          )}
        </div>
        <p className="mt-1 text-body text-ink-muted">{event.description}</p>
        <div className="mt-md flex flex-wrap items-center gap-md text-label text-ink-muted">
          <span className="flex items-center gap-sm">
            <Clock className="h-4 w-4" /> {format(date, 'MMM d, yyyy h:mm a')}
          </span>
          <span className="flex items-center gap-sm">
            <Users className="h-4 w-4" /> {event.target_group}
          </span>
        </div>
      </div>
    </Card>
  );
}
