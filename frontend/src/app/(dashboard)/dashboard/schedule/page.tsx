'use client';

import { useQuery } from 'react-query';
import { Calendar as CalendarIcon, Clock, Users } from 'lucide-react';
import apiClient from '@/lib/api';
import { Schedule, PaginatedResponse } from '@/types';
import { format, isFuture, isPast, isToday } from 'date-fns';

export default function SchedulePage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Schedule>>('schedule', async () => {
    const response = await apiClient.get('/schedules');
    return response.data;
  });

  const upcomingEvents = data?.items.filter((event) => isFuture(new Date(event.event_date))) || [];
  const pastEvents = data?.items.filter((event) => isPast(new Date(event.event_date))) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Schedule</h1>
        <p className="text-gray-600 mt-1">View upcoming events and deadlines</p>
      </div>

      {/* Upcoming Events */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Upcoming Events</h2>
        <div className="grid gap-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
          ) : upcomingEvents.length > 0 ? (
            upcomingEvents.map((event) => <EventCard key={event.id} event={event} />)
          ) : (
            <div className="bg-white rounded-xl p-8 text-center">
              <CalendarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No upcoming events</p>
            </div>
          )}
        </div>
      </div>

      {/* Past Events */}
      {pastEvents.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Past Events</h2>
          <div className="grid gap-4">
            {pastEvents.map((event) => (
              <EventCard key={event.id} event={event} isPast />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EventCard({ event, isPast = false }: { event: Schedule; isPast?: boolean }) {
  const eventDate = new Date(event.event_date);
  const isEventToday = isToday(eventDate);

  return (
    <div
      className={`bg-white rounded-xl shadow-sm p-6 ${
        isPast ? 'opacity-60' : 'hover:shadow-md'
      } transition-shadow`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-xl font-semibold text-gray-900">{event.title}</h3>
            {isEventToday && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                Today
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">{event.description}</p>
          <div className="flex items-center space-x-6 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4" />
              <span>{format(eventDate, 'MMM d, yyyy h:mm a')}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>{event.target_group}</span>
            </div>
          </div>
        </div>
        <div className="ml-4">
          <div className="bg-primary-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-primary-600">
              {format(eventDate, 'd')}
            </div>
            <div className="text-sm text-primary-600">{format(eventDate, 'MMM')}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
