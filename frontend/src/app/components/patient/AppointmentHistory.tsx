import { useEffect, useState } from 'react';
import { Search, Calendar, Clock, User, AlertCircle } from 'lucide-react';
import { apiFetch, postJson } from '../../api';
import { StatusBadge } from '../shared/StatusBadge';
import type { Appointment, AppointmentStatus } from '../../types';

export function AppointmentHistory() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | 'All'>('All');
  const [cancelId, setCancelId] = useState<string | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => apiFetch<{ ok: boolean; appointments: Appointment[] }>('/api/appointments').then(d => setAppointments(d.appointments)).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const filtered = appointments.filter(a => {
    const matchSearch = a.doctorName.toLowerCase().includes(search.toLowerCase()) || a.reason.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'All' || a.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const handleCancel = async (id: string) => {
    try {
      await postJson(`/api/appointments/${id}/cancel`, {});
      await load();
      setCancelId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not cancel appointment.');
      setCancelId(null);
    }
  };

  if (loading) return <div className="text-slate-500">Loading appointments...</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {error && <div className="bg-red-50 border border-red-100 text-red-700 rounded-2xl p-4 text-sm">{error}</div>}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by doctor or reason" className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-900 placeholder:text-slate-400" />
        </div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as AppointmentStatus | 'All')} className="px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-700">
          {['All', 'Booked', 'Completed', 'Cancelled', 'Missed'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-100 p-12 text-center"><Calendar size={40} className="text-slate-300 mx-auto mb-4" /><p className="text-slate-500">No appointments found.</p></div>
      ) : (
        <div className="space-y-3">
          {filtered.map(a => (
            <div key={a.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0"><User size={18} className="text-blue-600" /></div>
                  <div>
                    <p className="font-semibold text-slate-900">{a.doctorName}</p>
                    <p className="text-sm text-slate-500">{a.specialisation}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                      <span className="flex items-center gap-1"><Calendar size={14} className="text-slate-400" />{new Date(a.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                      <span className="flex items-center gap-1"><Clock size={14} className="text-slate-400" />{a.time}</span>
                    </div>
                    {a.reason && <p className="text-sm text-slate-400 mt-1">Reason: {a.reason}</p>}
                  </div>
                </div>
                <div className="flex flex-col items-start sm:items-end gap-2">
                  <StatusBadge status={a.status} />
                  {a.status === 'Booked' && new Date(a.date) >= new Date(new Date().toDateString()) && <button onClick={() => setCancelId(a.id)} className="text-sm text-red-600 hover:text-red-700 font-medium px-3 py-1 rounded-lg hover:bg-red-50 transition-colors">Cancel</button>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {cancelId && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-xl p-8 max-w-sm w-full">
            <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4"><AlertCircle size={24} className="text-red-600" /></div>
            <h3 className="font-bold text-slate-900 text-xl text-center mb-2">Cancel appointment?</h3>
            <p className="text-slate-500 text-center mb-6">This appointment can still be cancelled. Are you sure?</p>
            <div className="flex gap-3"><button onClick={() => setCancelId(null)} className="flex-1 py-3 border border-slate-200 text-slate-700 font-medium rounded-xl hover:bg-slate-50 transition-colors">Keep it</button><button onClick={() => handleCancel(cancelId)} className="flex-1 py-3 bg-red-600 text-white font-semibold rounded-xl hover:bg-red-700 transition-colors">Yes, cancel</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
