import { useEffect, useState } from 'react';
import { Download, BarChart3, FileText, Calendar, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { apiFetch } from '../../api';

interface Summary {
  appointments: number;
  completedAppointments: number;
  cancelledAppointments: number;
  prescriptions: number;
  paidPrescriptions: number;
}

const pieColors = ['#2563eb', '#14b8a6', '#f59e0b'];

export function Reports() {
  const [summary, setSummary] = useState<Summary | null>(null);
  useEffect(() => { apiFetch<{ ok: boolean; summary: Summary }>('/api/reports/summary').then(d => setSummary(d.summary)); }, []);

  const pendingAppointments = summary ? Math.max(summary.appointments - summary.completedAppointments - summary.cancelledAppointments, 0) : 0;
  const pendingPrescriptions = summary ? Math.max(summary.prescriptions - summary.paidPrescriptions, 0) : 0;

  const appointmentChart = summary ? [
    { label: 'Completed', value: summary.completedAppointments },
    { label: 'Cancelled', value: summary.cancelledAppointments },
    { label: 'Booked/Missed', value: pendingAppointments },
  ] : [];

  const prescriptionChart = summary ? [
    { label: 'Paid', value: summary.paidPrescriptions },
    { label: 'Pending', value: pendingPrescriptions },
  ] : [];

  const reports = [
    {
      title: 'Appointment report',
      desc: 'Download appointment records including patient, staff, date, time and status.',
      href: '/reports/appointments.csv',
      icon: <Calendar size={22} className="text-blue-600" />,
      bg: 'bg-blue-50',
      stats: summary ? [
        { label: 'Total appointments', value: summary.appointments },
        { label: 'Completed', value: summary.completedAppointments },
        { label: 'Cancelled', value: summary.cancelledAppointments },
        { label: 'Booked/Missed', value: pendingAppointments },
      ] : [],
    },
    {
      title: 'Prescription report',
      desc: 'Download prescription workflow records and payment status information.',
      href: '/reports/prescriptions.csv',
      icon: <FileText size={22} className="text-teal-600" />,
      bg: 'bg-teal-50',
      stats: summary ? [
        { label: 'Total requests', value: summary.prescriptions },
        { label: 'Paid prescriptions', value: summary.paidPrescriptions },
        { label: 'Pending payment/review', value: pendingPrescriptions },
      ] : [],
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex items-center gap-2 text-slate-600">
          <BarChart3 size={18} />
          <span className="font-medium text-sm">Reporting period:</span>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-500">From</label>
            <input type="date" className="px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-700 text-sm" />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-500">To</label>
            <input type="date" className="px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-700 text-sm" />
          </div>
          <button className="px-5 py-2 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors text-sm">
            Apply
          </button>
        </div>
      </div>

      {!summary ? (
        <div className="text-slate-500">Loading reports...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center"><Calendar size={20} className="text-blue-600" /></div>
                <div>
                  <h3 className="font-semibold text-slate-900">Appointment status overview</h3>
                  <p className="text-sm text-slate-500">Visual breakdown of appointment outcomes.</p>
                </div>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={appointmentChart} margin={{ top: 10, right: 18, bottom: 0, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: 12, borderColor: '#e2e8f0' }} />
                    <Bar dataKey="value" radius={[10, 10, 0, 0]} fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 bg-teal-50 rounded-xl flex items-center justify-center"><FileText size={20} className="text-teal-600" /></div>
                <div>
                  <h3 className="font-semibold text-slate-900">Prescription payment overview</h3>
                  <p className="text-sm text-slate-500">Shows paid and pending prescription records.</p>
                </div>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={prescriptionChart} dataKey="value" nameKey="label" innerRadius={60} outerRadius={90} paddingAngle={4}>
                      {prescriptionChart.map((_, index) => <Cell key={`slice-${index}`} fill={pieColors[index % pieColors.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 12, borderColor: '#e2e8f0' }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {reports.map(r => (
              <div key={r.title} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${r.bg} rounded-xl flex items-center justify-center`}>{r.icon}</div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{r.title}</h3>
                      <p className="text-sm text-slate-500">{r.desc}</p>
                    </div>
                  </div>
                  <a href={r.href} download className="flex items-center gap-1.5 px-4 py-2 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50 transition-colors text-sm">
                    <Download size={14} /> Download CSV
                  </a>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {r.stats.map(s => (
                    <div key={s.label} className="bg-slate-50 rounded-2xl p-4">
                      <p className="text-2xl font-bold text-slate-900">{s.value}</p>
                      <p className="text-xs text-slate-500 mt-1">{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-3">
            <Clock size={18} className="text-amber-600 mt-0.5" />
            <p className="text-sm text-amber-800">CSV exports are generated from the current database records, so the report values update as appointments and prescriptions are created or changed.</p>
          </div>
        </>
      )}
    </div>
  );
}
