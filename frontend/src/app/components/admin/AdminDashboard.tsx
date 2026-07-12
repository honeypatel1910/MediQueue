import { useEffect, useState } from 'react';
import { Activity, CalendarDays, ClipboardList, FileText, ShieldCheck, Users, UserCheck } from 'lucide-react';
import { apiFetch } from '../../api';
import type { Appointment, Prescription } from '../../types';
import { StatusBadge } from '../shared/StatusBadge';

interface AdminSummary {
  totalUsers: number;
  activeUsers: number;
  patients: number;
  doctors: number;
  nurses: number;
  todayAppointments: number;
  upcomingAppointments: number;
  pendingPrescriptions: number;
  approvedPrescriptions: number;
  paidPrescriptions: number;
}

interface AuditEntry {
  id: string;
  action: string;
  entityType: string;
  details: string;
  createdAt: string;
  userName: string;
}

interface AdminDashboardResponse {
  ok: boolean;
  summary: AdminSummary;
  recentAppointments: Appointment[];
  recentPrescriptions: Prescription[];
  recentAuditLogs: AuditEntry[];
}

const defaultSummary: AdminSummary = {
  totalUsers: 0,
  activeUsers: 0,
  patients: 0,
  doctors: 0,
  nurses: 0,
  todayAppointments: 0,
  upcomingAppointments: 0,
  pendingPrescriptions: 0,
  approvedPrescriptions: 0,
  paidPrescriptions: 0,
};

function formatDate(value: string) {
  if (!value) return 'Not scheduled';
  return new Date(value).toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function AdminDashboard() {
  const [summary, setSummary] = useState<AdminSummary>(defaultSummary);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadDashboard() {
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch<AdminDashboardResponse>('/api/admin/dashboard');
      setSummary(data.summary || defaultSummary);
      setAppointments(data.recentAppointments || []);
      setPrescriptions(data.recentPrescriptions || []);
      setAuditLogs(data.recentAuditLogs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load admin dashboard.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return <div className="rounded-3xl border border-slate-100 bg-white p-8 text-slate-500 shadow-sm">Loading practice overview...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Practice Admin</p>
            <h2 className="mt-2 text-3xl font-bold text-slate-950">Practice Overview</h2>
            <p className="mt-3 max-w-3xl text-slate-500">
              Monitor users, appointments, prescription activity and recent system actions from one workspace.
            </p>
          </div>
          <button
            onClick={loadDashboard}
            className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>
      </section>

      {error && <div className="rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        <SummaryCard icon={<Users size={22} />} label="Total users" value={summary.totalUsers} detail={`${summary.activeUsers} active accounts`} />
        <SummaryCard icon={<UserCheck size={22} />} label="Clinical staff" value={summary.doctors + summary.nurses} detail={`${summary.doctors} doctors · ${summary.nurses} nurses`} />
        <SummaryCard icon={<CalendarDays size={22} />} label="Appointments today" value={summary.todayAppointments} detail={`${summary.upcomingAppointments} upcoming booked`} />
        <SummaryCard icon={<FileText size={22} />} label="Pending prescriptions" value={summary.pendingPrescriptions} detail={`${summary.paidPrescriptions} paid prescriptions`} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-2xl bg-blue-50 p-3 text-blue-600"><ClipboardList size={20} /></div>
            <div>
              <h3 className="text-lg font-semibold text-slate-950">Recent appointments</h3>
              <p className="text-sm text-slate-500">Latest GP appointment activity.</p>
            </div>
          </div>
          <div className="space-y-3">
            {appointments.length === 0 && <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">No appointments recorded yet.</p>}
            {appointments.map((appointment) => (
              <div key={appointment.id} className="rounded-2xl border border-slate-100 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-900">{appointment.patientName}</p>
                    <p className="text-sm text-slate-500">{appointment.doctorName} · {appointment.date} {appointment.time}</p>
                    {appointment.reason && <p className="mt-2 text-sm text-slate-600">{appointment.reason}</p>}
                  </div>
                  <StatusBadge status={appointment.status} />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-2xl bg-purple-50 p-3 text-purple-600"><FileText size={20} /></div>
            <div>
              <h3 className="text-lg font-semibold text-slate-950">Recent prescriptions</h3>
              <p className="text-sm text-slate-500">Latest medicine request and payment activity.</p>
            </div>
          </div>
          <div className="space-y-3">
            {prescriptions.length === 0 && <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">No prescription requests recorded yet.</p>}
            {prescriptions.map((prescription) => (
              <div key={prescription.id} className="rounded-2xl border border-slate-100 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-slate-900">{prescription.medicine}</p>
                    <p className="text-sm text-slate-500">{prescription.patientName} · {prescription.quantity}</p>
                    {prescription.reason && <p className="mt-2 text-sm text-slate-600">{prescription.reason}</p>}
                  </div>
                  <div className="space-y-2 text-right">
                    <StatusBadge status={prescription.status} />
                    <StatusBadge status={prescription.paymentStatus} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600"><ShieldCheck size={20} /></div>
          <div>
            <h3 className="text-lg font-semibold text-slate-950">Recent system activity</h3>
            <p className="text-sm text-slate-500">Audit trail for important actions.</p>
          </div>
        </div>
        <div className="space-y-3">
          {auditLogs.length === 0 && <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">No audit activity recorded yet.</p>}
          {auditLogs.map((log) => (
            <div key={log.id} className="flex flex-col gap-2 rounded-2xl border border-slate-100 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Activity size={16} className="text-blue-600" />
                  <p className="font-semibold text-slate-900">{log.action}</p>
                </div>
                <p className="mt-1 text-sm text-slate-500">{log.userName} · {log.entityType}</p>
                {log.details && <p className="mt-1 text-sm text-slate-600">{log.details}</p>}
              </div>
              <p className="text-sm text-slate-400">{formatDate(log.createdAt)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function SummaryCard({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: number; detail: string }) {
  return (
    <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
      <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">{icon}</div>
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </section>
  );
}
