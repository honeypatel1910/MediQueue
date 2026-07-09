import { useEffect, useMemo, useState } from 'react';
import { Bell, Calendar, CheckCircle, CreditCard, FileText, XCircle } from 'lucide-react';
import { apiFetch, postJson } from '../api';
import { useApp } from '../AppContext';
import type { Notification } from '../types';

function iconForNotification(type: Notification['type']) {
  if (type === 'appointment_cancelled') return <XCircle size={20} className="text-red-600" />;
  if (type === 'prescription_ready') return <CheckCircle size={20} className="text-teal-600" />;
  if (type === 'payment_received') return <CreditCard size={20} className="text-amber-600" />;
  if (type === 'prescription_approved') return <FileText size={20} className="text-green-600" />;
  return <Calendar size={20} className="text-blue-600" />;
}

export function Notifications() {
  const { setUnreadCount } = useApp();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const unreadCount = useMemo(() => notifications.filter((item) => !item.read).length, [notifications]);

  const loadNotifications = async () => {
    setError('');
    const data = await apiFetch<{ ok: boolean; notifications: Notification[] }>('/api/notifications');
    setNotifications(data.notifications || []);
    setUnreadCount((data.notifications || []).filter((item) => !item.read).length);
  };

  useEffect(() => {
    loadNotifications()
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load notifications.'))
      .finally(() => setLoading(false));
  }, []);

  const markRead = async (id: string) => {
    await postJson(`/api/notifications/${id}/read`, {});
    await loadNotifications();
  };

  const markAllRead = async () => {
    const unread = notifications.filter((item) => !item.read);
    for (const item of unread) {
      await postJson(`/api/notifications/${item.id}/read`, {});
    }
    await loadNotifications();
  };

  if (loading) {
    return <div className="text-slate-500">Loading notifications...</div>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-bold text-slate-900">
            <Bell size={20} className="text-blue-600" />
            Notifications
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {unreadCount} unread notification{unreadCount === 1 ? '' : 's'}
          </p>
        </div>
        {unreadCount > 0 && (
          <button onClick={markAllRead} className="text-sm font-medium text-blue-600 hover:text-blue-700">
            Mark all read
          </button>
        )}
      </div>

      {error && <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="space-y-3">
        {notifications.map((item) => (
          <button
            key={item.id}
            onClick={() => !item.read && markRead(item.id)}
            className={`w-full rounded-2xl border bg-white p-5 text-left shadow-sm transition-all ${
              item.read ? 'border-slate-100' : 'border-blue-100 ring-1 ring-blue-50'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${item.read ? 'bg-slate-50' : 'bg-blue-50'}`}>
                {iconForNotification(item.type)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-slate-900">{item.title}</p>
                  {!item.read && <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full bg-blue-600" />}
                </div>
                <p className="mt-1 text-sm text-slate-500">{item.message}</p>
                <p className="mt-2 text-xs text-slate-400">{new Date(item.timestamp).toLocaleString('en-GB')}</p>
              </div>
            </div>
          </button>
        ))}

        {notifications.length === 0 && (
          <div className="rounded-2xl border border-slate-100 bg-white p-12 text-center">
            <Bell size={40} className="mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500">No notifications yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
