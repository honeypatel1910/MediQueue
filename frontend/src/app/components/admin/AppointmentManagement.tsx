import { useEffect, useState } from 'react';
import { Calendar, Search } from 'lucide-react';
import { apiFetch, postJson } from '../../api';
import { StatusBadge } from '../shared/StatusBadge';
import type { Appointment, AppointmentStatus } from '../../types';

export function AppointmentManagement() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | 'All'>('All');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const loadAppointments = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<{ ok: boolean; appointments: Appointment[] }>('/api/admin/appointments');
      setAppointments(data.appointments);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  const updateStatus = async (id: string, status: AppointmentStatus) => {
    setMessage('');
    try {
      await postJson(`/api/staff/appointments/${id}/status`, { status });
      await loadAppointments();
      setMessage('Appointment updated successfully.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not update appointment.');
    }
  };

  const filtered = appointments.filter((appointment) => {
    const query = search.toLowerCase();
    const matchesStatus = statusFilter === 'All' || appointment.status === statusFilter;
    const matchesSearch =
      !query ||
      appointment.patientName.toLowerCase().includes(query) ||
      appointment.doctorName.toLowerCase().includes(query) ||
      appointment.reason.toLowerCase().includes(query);
    return matchesStatus && matchesSearch;
  });

  if (loading) {
    return <div className="text-slate-500">Loading appointments...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search patient, staff or reason"
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as AppointmentStatus | 'All')}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option>All</option>
          <option>Booked</option>
          <option>Pending Approval</option>
          <option>Completed</option>
          <option>Cancelled</option>
          <option>Missed</option>
          <option>Rejected</option>
        </select>
      </div>

      {message && <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">{message}</div>}

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="p-4 text-left">Patient</th>
                <th className="p-4 text-left">Staff</th>
                <th className="p-4 text-left">Date/Time</th>
                <th className="p-4 text-left">Reason</th>
                <th className="p-4 text-left">Status</th>
                <th className="p-4 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((appointment) => (
                <tr key={appointment.id} className="border-t border-slate-100">
                  <td className="p-4 font-medium text-slate-900">{appointment.patientName}</td>
                  <td className="p-4 text-slate-600">
                    {appointment.doctorName}
                    <br />
                    <span className="text-xs text-slate-400">{appointment.specialisation}</span>
                  </td>
                  <td className="p-4 text-slate-500">
                    {appointment.date ? new Date(appointment.date).toLocaleDateString('en-GB') : '-'}
                    <br />
                    {appointment.time}
                  </td>
                  <td className="max-w-xs p-4 text-slate-500">{appointment.reason || '-'}</td>
                  <td className="p-4"><StatusBadge status={appointment.status} /></td>
                  <td className="p-4">
                    <select
                      value={appointment.status}
                      onChange={(event) => updateStatus(appointment.id, event.target.value as AppointmentStatus)}
                      className="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-slate-600"
                    >
                      <option>Booked</option>
                      <option>Pending Approval</option>
                      <option>Completed</option>
                      <option>Cancelled</option>
                      <option>Missed</option>
                      <option>Rejected</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="p-12 text-center">
            <Calendar size={40} className="mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500">No appointments found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
