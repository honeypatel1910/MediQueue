import { useEffect, useState } from 'react';
import { Calendar, ChevronRight, Clock, PlusCircle } from 'lucide-react';
import { apiFetch } from '../../api';
import { useApp } from '../../AppContext';
import type { Appointment } from '../../types';
import { StatusBadge } from '../shared/StatusBadge';

interface StaffDashboardResponse {
  ok: boolean;
  todayAppointments: Appointment[];
  schedule: Appointment[];
}

export function NurseDashboard() {
  const { currentUser, setCurrentPage } = useApp();
  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [schedule, setSchedule] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch<StaffDashboardResponse>('/api/staff/dashboard')
      .then((data) => {
        setTodayAppointments(data.todayAppointments || []);
        setSchedule(data.schedule || []);
      })
      .catch((err) => setError(err.message || 'Unable to load dashboard.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-500">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Hello, {currentUser?.name}</h2>
        <p className="text-slate-500">Manage nursing appointments and your availability.</p>
      </div>

      {error && <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <button onClick={() => setCurrentPage('nurse-schedule')} className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm transition-all hover:shadow-md">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50">
            <Calendar size={22} className="text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{todayAppointments.length}</p>
          <p className="text-sm text-slate-500">Appointments today</p>
        </button>

        <button onClick={() => setCurrentPage('nurse-availability')} className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm transition-all hover:shadow-md">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50">
            <PlusCircle size={22} className="text-teal-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">New</p>
          <p className="text-sm text-slate-500">Add availability</p>
        </button>
      </div>

      <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Upcoming schedule</h3>
          <button onClick={() => setCurrentPage('nurse-schedule')} className="flex items-center gap-1 text-sm text-blue-600">
            View all <ChevronRight size={14} />
          </button>
        </div>
        <div className="space-y-3">
          {schedule.slice(0, 8).map((appointment) => (
            <div key={appointment.id} className="rounded-xl bg-slate-50 p-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{appointment.patientName}</p>
                  <p className="flex items-center gap-1 text-xs text-slate-500">
                    <Clock size={12} /> {appointment.date ? new Date(appointment.date).toLocaleDateString('en-GB') : ''} {appointment.time}
                  </p>
                </div>
                <StatusBadge status={appointment.status} />
              </div>
            </div>
          ))}
          {schedule.length === 0 && <p className="text-sm text-slate-500">No appointments in your schedule.</p>}
        </div>
      </section>
    </div>
  );
}
