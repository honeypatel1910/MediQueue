import { useEffect, useMemo, useState } from 'react';
import { Download, BarChart3, FileText, Calendar, Clock, Filter, X } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { apiFetch } from '../../api';

interface ReportFilters {
  start_date: string;
  end_date: string;
}

interface Summary {
  appointments: number;
  completedAppointments: number;
  cancelledAppointments: number;
  bookedAppointments?: number;
  pendingApprovalAppointments?: number;
  missedAppointments?: number;
  rejectedAppointments?: number;
  prescriptions: number;
  paidPrescriptions: number;
  pendingPaymentPrescriptions?: number;
  requestedPrescriptions?: number;
  underReviewPrescriptions?: number;
  approvedPrescriptions?: number;
  readyPrescriptions?: number;
  collectedPrescriptions?: number;
  rejectedPrescriptions?: number;
  periodLabel?: string;
  filters?: ReportFilters;
}

const pieColors = ['#2563eb', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b'];

function buildQuery(startDate: string, endDate: string) {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function Reports() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [appliedStartDate, setAppliedStartDate] = useState('');
  const [appliedEndDate, setAppliedEndDate] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const loadSummary = async (start = appliedStartDate, end = appliedEndDate) => {
    setLoading(true);
    setMessage('');
    try {
      const data = await apiFetch<{ ok: boolean; summary: Summary }>(`/api/reports/summary${buildQuery(start, end)}`);
      setSummary(data.summary);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not load report summary.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary('', '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyFilters = async () => {
    if (startDate && endDate && startDate > endDate) {
      setMessage('The start date cannot be after the end date.');
      return;
    }
    setAppliedStartDate(startDate);
    setAppliedEndDate(endDate);
    await loadSummary(startDate, endDate);
  };

  const clearFilters = async () => {
    setStartDate('');
    setEndDate('');
    setAppliedStartDate('');
    setAppliedEndDate('');
    await loadSummary('', '');
  };

  const downloadQuery = useMemo(() => buildQuery(appliedStartDate, appliedEndDate), [appliedStartDate, appliedEndDate]);

  const bookedAppointments = summary?.bookedAppointments ?? 0;
  const pendingApprovalAppointments = summary?.pendingApprovalAppointments ?? 0;
  const missedAppointments = summary?.missedAppointments ?? 0;
  const rejectedAppointments = summary?.rejectedAppointments ?? 0;
  const fallbackPendingAppointments = summary
    ? Math.max(summary.appointments - summary.completedAppointments - summary.cancelledAppointments, 0)
    : 0;

  const appointmentChart = summary ? [
    { label: 'Booked', value: bookedAppointments || fallbackPendingAppointments },
    { label: 'Pending Approval', value: pendingApprovalAppointments },
    { label: 'Completed', value: summary.completedAppointments },
    { label: 'Cancelled', value: summary.cancelledAppointments },
    { label: 'Missed', value: missedAppointments },
    { label: 'Rejected', value: rejectedAppointments },
  ].filter(item => item.value > 0 || item.label === 'Booked') : [];

  const prescriptionChart = summary ? [
    { label: 'Requested', value: summary.requestedPrescriptions ?? 0 },
    { label: 'Under Review', value: summary.underReviewPrescriptions ?? 0 },
    { label: 'Approved', value: summary.approvedPrescriptions ?? 0 },
    { label: 'Ready', value: summary.readyPrescriptions ?? 0 },
    { label: 'Collected', value: summary.collectedPrescriptions ?? 0 },
    { label: 'Rejected', value: summary.rejectedPrescriptions ?? 0 },
  ].filter(item => item.value > 0 || item.label === 'Requested') : [];

  const pendingPrescriptions = summary
    ? Math.max(summary.prescriptions - (summary.paidPrescriptions ?? 0), 0)
    : 0;

  const reports = [
    {
      title: 'Appointment report',
      desc: 'Download appointment records including patient, staff, date, time and status.',
      csvHref: `/reports/appointments.csv${downloadQuery}`,
      pdfHref: `/reports/appointments.pdf${downloadQuery}`,
      icon: <Calendar size={22} className="text-blue-600" />,
      bg: 'bg-blue-50',
      stats: summary ? [
        { label: 'Total appointments', value: summary.appointments },
        { label: 'Booked', value: bookedAppointments || fallbackPendingAppointments },
        { label: 'Pending approval', value: pendingApprovalAppointments },
        { label: 'Completed', value: summary.completedAppointments },
      ] : [],
    },
    {
      title: 'Prescription report',
      desc: 'Download prescription workflow records and payment status information.',
      csvHref: `/reports/prescriptions.csv${downloadQuery}`,
      pdfHref: `/reports/prescriptions.pdf${downloadQuery}`,
      icon: <FileText size={22} className="text-teal-600" />,
      bg: 'bg-teal-50',
      stats: summary ? [
        { label: 'Total requests', value: summary.prescriptions },
        { label: 'Paid prescriptions', value: summary.paidPrescriptions },
        { label: 'Pending payment/review', value: pendingPrescriptions },
        { label: 'Rejected', value: summary.rejectedPrescriptions ?? 0 },
      ] : [],
    },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2 text-slate-600">
          <BarChart3 size={18} />
          <span className="text-sm font-medium">Reporting period</span>
          {summary?.periodLabel && <span className="text-sm text-slate-400">- {summary.periodLabel}</span>}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-sm text-slate-500">From</label>
            <input
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-sm text-slate-500">To</label>
            <input
              type="date"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="button"
            onClick={applyFilters}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            <Filter size={15} /> Apply
          </button>
          <button
            type="button"
            onClick={clearFilters}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-5 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
          >
            <X size={15} /> Clear
          </button>
        </div>

        {message && <div className="mt-4 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">{message}</div>}
      </div>

      {loading && !summary ? (
        <div className="text-slate-500">Loading reports...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50"><Calendar size={20} className="text-blue-600" /></div>
                <div>
                  <h3 className="font-semibold text-slate-900">Appointment status overview</h3>
                  <p className="text-sm text-slate-500">Visual breakdown using the selected reporting period.</p>
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

            <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50"><FileText size={20} className="text-teal-600" /></div>
                <div>
                  <h3 className="font-semibold text-slate-900">Prescription status overview</h3>
                  <p className="text-sm text-slate-500">Shows prescription outcomes for the selected period.</p>
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
              <div key={r.title} className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
                <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 ${r.bg} items-center justify-center rounded-xl`}>{r.icon}</div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{r.title}</h3>
                      <p className="text-sm text-slate-500">{r.desc}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <a href={r.csvHref} download className="flex items-center gap-1.5 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50">
                      <Download size={14} /> CSV
                    </a>
                    <a href={r.pdfHref} download className="flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700">
                      <Download size={14} /> PDF
                    </a>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  {r.stats.map(s => (
                    <div key={s.label} className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-2xl font-bold text-slate-900">{s.value}</p>
                      <p className="mt-1 text-xs text-slate-500">{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <Clock size={18} className="mt-0.5 text-amber-600" />
            <p className="text-sm text-amber-800">CSV and PDF exports now use the selected reporting period. Clear the dates to export all records.</p>
          </div>
        </>
      )}
    </div>
  );
}
