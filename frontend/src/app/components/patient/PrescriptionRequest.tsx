import { useState } from 'react';
import { AlertCircle, CheckCircle, FileText } from 'lucide-react';
import { postJson } from '../../api';
import { useApp } from '../../AppContext';

export function PrescriptionRequest() {
  const { setCurrentPage } = useApp();
  const [form, setForm] = useState({ medicine: '', quantity: '', reason: '' });
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field: keyof typeof form, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (!form.medicine.trim() || !form.quantity.trim()) {
      setError('Medicine name and quantity are required.');
      return;
    }

    setLoading(true);
    try {
      await postJson('/api/prescriptions/request', form);
      setSubmitted(true);
      setForm({ medicine: '', quantity: '', reason: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit prescription request.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="mx-auto max-w-lg">
        <div className="rounded-3xl border border-slate-100 bg-white p-8 text-center shadow-sm md:p-10">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle size={32} className="text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold text-slate-900">Prescription requested</h2>
          <p className="mb-8 text-slate-500">
            Your request has been sent for review. You can track the status from your prescription history.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => setCurrentPage('prescription-history')}
              className="flex-1 rounded-xl bg-blue-600 py-3 font-semibold text-white transition-colors hover:bg-blue-700"
            >
              View prescriptions
            </button>
            <button
              type="button"
              onClick={() => setCurrentPage('patient-dashboard')}
              className="flex-1 rounded-xl border border-slate-200 py-3 font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm md:p-8">
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50">
          <FileText size={26} className="text-teal-600" />
        </div>
        <h2 className="mb-2 text-xl font-bold text-slate-900">Request a prescription</h2>
        <p className="mb-6 text-slate-500">Submit a repeat prescription request for review by the surgery.</p>

        {error && (
          <div className="mb-5 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4">
            <AlertCircle size={18} className="mt-0.5 text-red-600" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Medicine name</label>
            <input
              value={form.medicine}
              onChange={(event) => update('medicine', event.target.value)}
              placeholder="e.g. Salbutamol Inhaler"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Quantity</label>
            <input
              value={form.quantity}
              onChange={(event) => update('quantity', event.target.value)}
              placeholder="e.g. 1 inhaler or 28 tablets"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Reason / notes</label>
            <textarea
              value={form.reason}
              onChange={(event) => update('reason', event.target.value)}
              placeholder="Add any notes for the clinician"
              className="min-h-28 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            disabled={loading}
            className="w-full rounded-xl bg-blue-600 py-3 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? 'Submitting...' : 'Submit request'}
          </button>
        </form>
      </div>
    </div>
  );
}
