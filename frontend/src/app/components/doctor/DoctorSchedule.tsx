import { useEffect, useState } from 'react';
import { AlertCircle, Calendar, CheckCircle2, Clock, Search, User, Download } from 'lucide-react';
import { apiFetch, postJson } from '../../api';
import { StatusBadge } from '../shared/StatusBadge';
import type { Appointment, AppointmentStatus } from '../../types';

export function DoctorSchedule({ staffName }: { staffName: string }) {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<AppointmentStatus | 'All'>('All');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    const data = await apiFetch<{ ok: boolean; appointments: Appointment[] }>('/api/staff/schedule');
    setAppointments(data.appointments);
    setLoading(false);
  };

  useEffect(() => {
    load().catch((err) => {
      setError(err instanceof Error ? err.message : 'Schedule could not be loaded.');
      setLoading(false);
    });
  }, []);

  const updateStatus = async (id: string, newStatus: AppointmentStatus) => {
    setMessage('');
    setError('');
    try {
      await postJson(`/api/staff/appointments/${id}/status`, { status: newStatus });
      await load();
      setMessage('Appointment updated.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update appointment.');
    }
  };

  const approveExtra = async (id: string) => {
    setMessage('');
    setError('');
    try {
      await postJson(`/api/staff/appointments/${id}/approve-extra`, {});
      await load();
      setMessage('Extra appointment request approved.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not approve request.');
    }
  };

  const rejectExtra = async (id: string) => {
    setMessage('');
    setError('');
    try {
      await postJson(`/api/staff/appointments/${id}/reject-extra`, {});
      await load();
      setMessage('Extra appointment request rejected and the slot was released.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reject request.');
    }
  };

  const filtered = appointments.filter(
    (a) =>
      (status === 'All' || a.status === status) &&
      (!search ||
        a.patientName.toLowerCase().includes(search.toLowerCase()) ||
        a.reason.toLowerCase().includes(search.toLowerCase())),
  );

  if (loading) return <div className="text-slate-500">Loading schedule...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-2xl border border-slate-100 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-semibold text-slate-900">Schedule for {staffName}</p>
          <p className="text-sm text-slate-500">
            Update appointments, approve extra appointment requests, and export confirmed bookings to calendar.
          </p>
        </div>
        <a
          href="/api/staff/schedule/calendar"
          download
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          <Download size={16} />
          Export Schedule
        </a>
      </div>

      {message && (
        <div className="flex items-start gap-3 rounded-2xl border border-green-100 bg-green-50 p-4 text-sm text-green-700">
          <CheckCircle2 size={18} className="mt-0.5" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle size={18} className="mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search patient or reason"
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as AppointmentStatus | 'All')}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {['All', 'Booked', 'Pending Approval', 'Completed', 'Cancelled', 'Missed', 'Rejected'].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="space-y-3">
        {filtered.map((a) => (
          <div key={a.id} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50">
                  <User size={18} className="text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-slate-900">{a.patientName}</p>
                  <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar size={14} />
                      {new Date(a.date).toLocaleDateString('en-GB')}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={14} />
                      {a.time}
                    </span>
                  </div>
                  {a.reason && <p className="mt-2 text-sm text-slate-500">Reason: {a.reason}</p>}
                  {a.status === 'Pending Approval' && (
                    <p className="mt-2 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-700">
                      This patient already has 3 active upcoming appointments with you. Approve only if clinically needed.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-2 sm:items-end">
                <StatusBadge status={a.status} />
                {a.canExportCalendar && (
                  <a
                    href={a.calendarUrl || `/api/appointments/${a.id}/calendar`}
                    download
                    className="inline-flex items-center gap-1 rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                  >
                    <Download size={13} />
                    Calendar
                  </a>
                )}
                {a.status === 'Pending Approval' ? (
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => approveExtra(a.id)}
                      className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => rejectExtra(a.id)}
                      className="rounded-lg border border-amber-200 px-3 py-1.5 text-xs font-semibold text-amber-700 hover:bg-amber-50"
                    >
                      Reject
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {(['Completed', 'Missed', 'Cancelled'] as AppointmentStatus[]).map((s) => (
                      <button
                        key={s}
                        disabled={a.status === s || a.status === 'Rejected'}
                        onClick={() => updateStatus(a.id, s)}
                        className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="rounded-2xl border border-slate-100 bg-white p-12 text-center">
            <Calendar size={40} className="mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500">No appointments found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
