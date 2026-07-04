import { useEffect, useState } from 'react';
import { Calendar, ChevronRight, Clock, FileText, PlusCircle } from 'lucide-react';
import { apiFetch } from '../../api';
import { useApp } from '../../AppContext';
import type { Appointment, Prescription } from '../../types';
import { StatusBadge } from '../shared/StatusBadge';

interface StaffDashboardResponse {
  ok: boolean;
  todayAppointments: Appointment[];
  schedule: Appointment[];
  prescriptions: Prescription[];
}

export function DoctorDashboard() {
  const { currentUser, setCurrentPage } = useApp();
  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [schedule, setSchedule] = useState<Appointment[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch<StaffDashboardResponse>('/api/staff/dashboard')
      .then((data) => {
        setTodayAppointments(data.todayAppointments || []);
        setSchedule(data.schedule || []);
        setPrescriptions(data.prescriptions || []);
      })
      .catch((err) => setError(err.message || 'Unable to load dashboard.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-500">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Hello, {currentUser?.name}</h2>
        <p className="text-slate-500">Manage appointments, availability and prescription reviews.</p>
      </div>

      {error && <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <button onClick={() => setCurrentPage('doctor-schedule')} className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm transition-all hover:shadow-md">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50">
            <Calendar size={22} className="text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{todayAppointments.length}</p>
          <p className="text-sm text-slate-500">Appointments today</p>
        </button>

        <button onClick={() => setCurrentPage('doctor-prescriptions')} className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm transition-all hover:shadow-md">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50">
            <FileText size={22} className="text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{prescriptions.length}</p>
          <p className="text-sm text-slate-500">Pending prescriptions</p>
        </button>

        <button onClick={() => setCurrentPage('doctor-availability')} className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm transition-all hover:shadow-md">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50">
            <PlusCircle size={22} className="text-teal-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">New</p>
          <p className="text-sm text-slate-500">Add availability</p>
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900">Upcoming schedule</h3>
            <button onClick={() => setCurrentPage('doctor-schedule')} className="flex items-center gap-1 text-sm text-blue-600">
              View all <ChevronRight size={14} />
            </button>
          </div>
          <div className="space-y-3">
            {schedule.slice(0, 5).map((appointment) => (
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

        <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900">Prescription review queue</h3>
            <button onClick={() => setCurrentPage('doctor-prescriptions')} className="flex items-center gap-1 text-sm text-blue-600">
              Review <ChevronRight size={14} />
            </button>
          </div>
          <div className="space-y-3">
            {prescriptions.slice(0, 5).map((prescription) => (
              <div key={prescription.id} className="rounded-xl bg-slate-50 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{prescription.medicine}</p>
                    <p className="text-xs text-slate-500">{prescription.patientName}</p>
                  </div>
                  <StatusBadge status={prescription.status} />
                </div>
              </div>
            ))}
            {prescriptions.length === 0 && <p className="text-sm text-slate-500">No prescriptions waiting for review.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}
