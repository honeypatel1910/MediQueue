import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, FileText, Search, XCircle } from 'lucide-react';
import { apiFetch, postJson } from '../../api';
import type { Prescription } from '../../types';
import { StatusBadge } from '../shared/StatusBadge';

type PrescriptionResponse = {
  ok: boolean;
  prescriptions: Prescription[];
};

export function PrescriptionReview() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [search, setSearch] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadPrescriptions = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<PrescriptionResponse>('/api/prescriptions');
      setPrescriptions(data.prescriptions || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPrescriptions();
  }, []);

  const filteredPrescriptions = useMemo(() => {
    const query = search.trim().toLowerCase();
    return prescriptions.filter((prescription) => {
      const searchable = `${prescription.patientName} ${prescription.medicine} ${prescription.reason}`.toLowerCase();
      return !query || searchable.includes(query);
    });
  }, [prescriptions, search]);

  const updatePrescription = async (id: string, status: 'Under Review' | 'Approved' | 'Rejected') => {
    setMessage('');
    setUpdatingId(id);
    try {
      await postJson(`/api/prescriptions/${id}/review`, { status });
      await loadPrescriptions();
      setMessage(`Prescription marked as ${status}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not update prescription.');
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) {
    return <div className="rounded-2xl bg-white p-6 text-slate-500 shadow-sm">Loading prescription requests...</div>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50">
              <FileText className="text-blue-600" size={24} />
            </div>
            <h2 className="text-2xl font-bold text-slate-950">Prescription review</h2>
            <p className="mt-2 text-sm text-slate-500">
              Review patient prescription requests and update their clinical status.
            </p>
          </div>
        </div>
      </section>

      {message && (
        <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm font-medium text-blue-700">
          {message}
        </div>
      )}

      <section className="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search by patient, medicine or reason"
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
          />
        </div>
      </section>

      <section className="space-y-4">
        {filteredPrescriptions.map((prescription) => {
          const isUpdating = updatingId === prescription.id;
          return (
            <article key={prescription.id} className="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-semibold text-slate-950">{prescription.medicine}</h3>
                    <StatusBadge status={prescription.status} />
                  </div>
                  <p className="text-sm text-slate-500">
                    {prescription.quantity} requested by {prescription.patientName}
                  </p>
                  <p className="text-sm text-slate-500">
                    Requested: {prescription.requestedDate ? new Date(prescription.requestedDate).toLocaleDateString('en-GB') : 'Not recorded'}
                  </p>
                  {prescription.reason && <p className="text-sm text-slate-600">Reason: {prescription.reason}</p>}
                  {prescription.amountDue ? (
                    <p className="text-sm font-medium text-slate-700">Amount due: £{prescription.amountDue.toFixed(2)}</p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2 lg:justify-end">
                  <button
                    type="button"
                    onClick={() => updatePrescription(prescription.id, 'Under Review')}
                    disabled={isUpdating}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-60"
                  >
                    Under review
                  </button>
                  <button
                    type="button"
                    onClick={() => updatePrescription(prescription.id, 'Approved')}
                    disabled={isUpdating}
                    className="inline-flex items-center gap-2 rounded-xl bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
                  >
                    <CheckCircle2 size={16} /> Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => updatePrescription(prescription.id, 'Rejected')}
                    disabled={isUpdating}
                    className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
                  >
                    <XCircle size={16} /> Reject
                  </button>
                </div>
              </div>
            </article>
          );
        })}

        {filteredPrescriptions.length === 0 && (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-white p-10 text-center text-slate-500">
            No prescription requests found.
          </div>
        )}
      </section>
    </div>
  );
}
