import type { AppointmentStatus, PaymentStatus, PrescriptionStatus } from '../../types';

type AnyStatus = AppointmentStatus | PrescriptionStatus | PaymentStatus | string;

const statusConfig: Record<string, { bg: string; text: string; dot: string }> = {
  Booked: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500' },
  'Pending Approval': { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
  Completed: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  Cancelled: { bg: 'bg-slate-100', text: 'text-slate-600', dot: 'bg-slate-400' },
  Missed: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
  Requested: { bg: 'bg-slate-100', text: 'text-slate-600', dot: 'bg-slate-400' },
  'Under Review': { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
  Approved: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500' },
  'Ready for Collection': { bg: 'bg-teal-50', text: 'text-teal-700', dot: 'bg-teal-500' },
  Collected: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  Rejected: { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500' },
  'Not required': { bg: 'bg-slate-100', text: 'text-slate-500', dot: 'bg-slate-300' },
  Pending: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500' },
  Paid: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  Verified: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  Active: { bg: 'bg-green-50', text: 'text-green-700', dot: 'bg-green-500' },
  Inactive: { bg: 'bg-slate-100', text: 'text-slate-500', dot: 'bg-slate-300' },
};

export function StatusBadge({ status }: { status: AnyStatus }) {
  const cfg = statusConfig[status] ?? { bg: 'bg-slate-100', text: 'text-slate-600', dot: 'bg-slate-400' };

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-sm font-medium ${cfg.bg} ${cfg.text}`}>
      <span className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${cfg.dot}`} />
      {status}
    </span>
  );
}
