import { useEffect, useState } from 'react';
import { FileText, Search } from 'lucide-react';
import { apiFetch, postJson } from '../../api';
import { StatusBadge } from '../shared/StatusBadge';
import type { PaymentStatus, Prescription, PrescriptionStatus } from '../../types';

export function PrescriptionManagement() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<PrescriptionStatus | 'All'>('All');
  const [paymentFilter, setPaymentFilter] = useState<PaymentStatus | 'All'>('All');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);

  const loadPrescriptions = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<{ ok: boolean; prescriptions: Prescription[] }>('/api/admin/prescriptions');
      setPrescriptions(data.prescriptions);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrescriptions();
  }, []);

  const updateCollectionStatus = async (id: string, status: 'Ready for Collection' | 'Collected') => {
    setMessage('');
    try {
      await postJson(`/api/admin/prescriptions/${id}/status`, { status });
      await loadPrescriptions();
      setMessage('Prescription updated successfully.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not update prescription.');
    }
  };

  const filtered = prescriptions.filter((prescription) => {
    const query = search.toLowerCase();
    const matchesSearch =
      !query ||
      prescription.patientName.toLowerCase().includes(query) ||
      prescription.medicine.toLowerCase().includes(query) ||
      prescription.quantity.toLowerCase().includes(query);
    const matchesStatus = statusFilter === 'All' || prescription.status === statusFilter;
    const matchesPayment = paymentFilter === 'All' || prescription.paymentStatus === paymentFilter;
    return matchesSearch && matchesStatus && matchesPayment;
  });

  if (loading) {
    return <div className="text-slate-500">Loading prescriptions...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 xl:flex-row">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by patient, medicine or quantity"
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as PrescriptionStatus | 'All')}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option>All</option>
          <option>Requested</option>
          <option>Under Review</option>
          <option>Approved</option>
          <option>Ready for Collection</option>
          <option>Collected</option>
          <option>Rejected</option>
        </select>
        <select
          value={paymentFilter}
          onChange={(event) => setPaymentFilter(event.target.value as PaymentStatus | 'All')}
          className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option>All</option>
          <option>Not required</option>
          <option>Pending</option>
          <option>Paid</option>
        </select>
      </div>

      {message && <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">{message}</div>}

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="p-4 text-left">Patient</th>
                <th className="p-4 text-left">Medicine</th>
                <th className="p-4 text-left">Status</th>
                <th className="p-4 text-left">Payment</th>
                <th className="p-4 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((prescription) => (
                <tr key={prescription.id} className="border-t border-slate-100">
                  <td className="p-4 font-medium text-slate-900">{prescription.patientName}</td>
                  <td className="p-4 text-slate-600">
                    {prescription.medicine}
                    <br />
                    <span className="text-xs text-slate-400">{prescription.quantity}</span>
                  </td>
                  <td className="p-4"><StatusBadge status={prescription.status} /></td>
                  <td className="p-4"><StatusBadge status={prescription.paymentStatus} /></td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={!(prescription.status === 'Approved' && prescription.paymentStatus === 'Paid')}
                        onClick={() => updateCollectionStatus(prescription.id, 'Ready for Collection')}
                        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Ready
                      </button>
                      <button
                        type="button"
                        disabled={prescription.status !== 'Ready for Collection'}
                        onClick={() => updateCollectionStatus(prescription.id, 'Collected')}
                        className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        Collected
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="p-12 text-center">
            <FileText size={40} className="mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500">No prescriptions found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
