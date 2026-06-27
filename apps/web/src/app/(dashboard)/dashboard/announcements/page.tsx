'use client';

import { useQuery } from 'react-query';
import { Bell, Calendar, Users } from 'lucide-react';
import apiClient from '@/lib/api';
import { Announcement, PaginatedResponse } from '@/types';
import { format } from 'date-fns';

export default function AnnouncementsPage() {
  const { data, isLoading } = useQuery<PaginatedResponse<Announcement>>(
    'announcements',
    async () => {
      const response = await apiClient.get('/announcements');
      return response.data;
    }
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Announcements</h1>
        <p className="text-gray-600 mt-1">Stay updated with the latest news</p>
      </div>

      {/* Announcements */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : data?.items && data.items.length > 0 ? (
          data.items.map((announcement) => (
            <AnnouncementCard key={announcement.id} announcement={announcement} />
          ))
        ) : (
          <div className="bg-white rounded-xl p-12 text-center">
            <Bell className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No announcements</h3>
            <p className="text-gray-600">Check back later for updates</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AnnouncementCard({ announcement }: { announcement: Announcement }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <div className="bg-primary-100 rounded-full p-3">
            <Bell className="h-6 w-6 text-primary-600" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">{announcement.title}</h3>
          <p className="text-gray-700 mb-4 whitespace-pre-wrap">{announcement.content}</p>
          <div className="flex items-center space-x-6 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>{format(new Date(announcement.created_at), 'MMM d, yyyy h:mm a')}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>{announcement.target_group}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
