import { useEffect, useState } from 'react';
import { FileText, CreditCard } from 'lucide-react';
import { apiFetch } from '../../api';
import { useApp } from '../../AppContext';
import { StatusBadge } from '../shared/StatusBadge';
import type { Prescription } from '../../types';

export function PrescriptionHistory() {
  const { setCurrentPage, setSelectedPrescription } = useApp();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [statusFilter, setStatusFilter] = useState('All');
  const [loading, setLoading] = useState(true);

  useEffect(() => { apiFetch<{ ok: boolean; prescriptions: Prescription[] }>('/api/prescriptions').then(d => setPrescriptions(d.prescriptions)).finally(() => setLoading(false)); }, []);
  const filtered = prescriptions.filter(p => statusFilter === 'All' || p.status === statusFilter);
  const handlePayNow = (p: Prescription) => { setSelectedPrescription(p); setCurrentPage('prescription-payment'); };

  if (loading) return <div className="text-slate-500">Loading prescriptions...</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex flex-wrap gap-2">{['All', 'Requested', 'Under Review', 'Approved', 'Ready for Collection', 'Collected', 'Rejected'].map(s => <button key={s} onClick={() => setStatusFilter(s)} className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${statusFilter === s ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'}`}>{s}</button>)}</div>
      {filtered.length === 0 ? <div className="bg-white rounded-2xl border border-slate-100 p-12 text-center"><FileText size={40} className="text-slate-300 mx-auto mb-4" /><p className="text-slate-500">No prescriptions found.</p></div> : <div className="space-y-3">{filtered.map(p => <div key={p.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5"><div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3"><div><p className="font-semibold text-slate-900">{p.medicine}</p><p className="text-sm text-slate-500">{p.quantity}</p><p className="text-sm text-slate-400 mt-1">Requested {new Date(p.requestedDate).toLocaleDateString('en-GB')}</p>{p.reviewedBy && <p className="text-sm text-slate-400">Reviewed by {p.reviewedBy}</p>}{p.reason && <p className="text-sm text-slate-500 mt-2">{p.reason}</p>}</div><div className="flex flex-col items-start sm:items-end gap-2"><StatusBadge status={p.status} /><StatusBadge status={p.paymentStatus} />{p.status === 'Rejected' && <p className="text-xs text-red-500 max-w-xs text-right">Please contact your GP for more information.</p>}{p.status === 'Approved' && p.paymentStatus === 'Pending' && <button onClick={() => handlePayNow(p)} className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors"><CreditCard size={15} />Pay now</button>}</div></div></div>)}</div>}
    </div>
  );
}
