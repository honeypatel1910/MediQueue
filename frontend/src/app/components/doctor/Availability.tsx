import { useEffect, useMemo, useState } from 'react';
import { CalendarClock, CheckCircle2, Edit3, MapPin, Save, XCircle } from 'lucide-react';
import { apiFetch } from '../../api';
import type { StaffAvailabilityBlock } from '../../types';

interface AvailabilityResponse {
  ok: boolean;
  availability: StaffAvailabilityBlock[];
}

interface AvailabilitySaveResponse {
  ok: boolean;
  availability: StaffAvailabilityBlock;
}

interface AvailabilityFormState {
  date: string;
  startTime: string;
  endTime: string;
  slotDuration: string;
  location: string;
}

function tomorrowDate() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
}

const emptyForm = (): AvailabilityFormState => ({
  date: tomorrowDate(),
  startTime: '10:00',
  endTime: '11:00',
  slotDuration: '20',
  location: 'GP Practice',
});

function countAvailableSlots(block: StaffAvailabilityBlock) {
  return block.slots.filter((slot) => slot.status === 'Available').length;
}

export function Availability() {
  const [availability, setAvailability] = useState<StaffAvailabilityBlock[]>([]);
  const [form, setForm] = useState<AvailabilityFormState>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const editingBlock = useMemo(
    () => availability.find((block) => block.id === editingId) || null,
    [availability, editingId],
  );

  const loadAvailability = async () => {
    setError('');
    const data = await apiFetch<AvailabilityResponse>('/api/staff/availability');
    setAvailability(data.availability || []);
  };

  useEffect(() => {
    loadAvailability()
      .catch((err) => setError(err.message || 'Availability could not be loaded.'))
      .finally(() => setLoading(false));
  }, []);

  const updateField = (field: keyof AvailabilityFormState, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const resetForm = () => {
    setEditingId(null);
    setForm(emptyForm());
  };

  const beginEdit = (block: StaffAvailabilityBlock) => {
    setError('');
    setMessage('');
    setEditingId(block.id);
    setForm({
      date: block.date,
      startTime: block.startTime,
      endTime: block.endTime,
      slotDuration: String(block.slotDuration),
      location: block.location || 'GP Practice',
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setSaving(true);

    const payload = {
      date: form.date,
      startTime: form.startTime,
      endTime: form.endTime,
      slotDuration: Number(form.slotDuration),
      location: form.location,
    };

    try {
      const url = editingId ? `/api/staff/availability/${editingId}` : '/api/staff/availability';
      const method = editingId ? 'PUT' : 'POST';
      const data = await apiFetch<AvailabilitySaveResponse>(url, {
        method,
        body: JSON.stringify(payload),
      });

      setAvailability((current) => {
        const withoutSaved = current.filter((block) => block.id !== data.availability.id);
        return [data.availability, ...withoutSaved].sort((a, b) => `${b.date} ${b.startTime}`.localeCompare(`${a.date} ${a.startTime}`));
      });

      setMessage(editingId ? 'Availability updated and slots regenerated.' : 'Availability created and slots generated.');
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Availability could not be saved.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm md:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Staff availability</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-950">Manage appointment availability</h2>
        <p className="mt-3 text-slate-500">
          Add working time and MediQueue will automatically create bookable appointment slots.
        </p>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[420px_1fr]">
        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-950">
                {editingId ? 'Edit availability' : 'Add availability'}
              </h3>
              {editingBlock && <p className="mt-1 text-sm text-slate-500">Update time or slot duration for this session.</p>}
            </div>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded-xl px-3 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100"
              >
                Cancel
              </button>
            )}
          </div>

          {error && (
            <div className="mb-4 flex items-start gap-2 rounded-2xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">
              <XCircle size={18} className="mt-0.5" />
              <span>{error}</span>
            </div>
          )}
          {message && (
            <div className="mb-4 flex items-start gap-2 rounded-2xl border border-green-100 bg-green-50 p-3 text-sm text-green-700">
              <CheckCircle2 size={18} className="mt-0.5" />
              <span>{message}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Date</span>
              <input
                type="date"
                value={form.date}
                onChange={(event) => updateField('date', event.target.value)}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                required
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Start time</span>
                <input
                  type="time"
                  value={form.startTime}
                  onChange={(event) => updateField('startTime', event.target.value)}
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  required
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">End time</span>
                <input
                  type="time"
                  value={form.endTime}
                  onChange={(event) => updateField('endTime', event.target.value)}
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  required
                />
              </label>
            </div>

            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Slot duration in minutes</span>
              <input
                type="number"
                min="5"
                max="120"
                value={form.slotDuration}
                onChange={(event) => updateField('slotDuration', event.target.value)}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                required
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700">Location</span>
              <input
                value={form.location}
                onChange={(event) => updateField('location', event.target.value)}
                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                required
              />
            </label>

            <button
              type="submit"
              disabled={saving}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {editingId ? <Save size={18} /> : <CalendarClock size={18} />}
              {saving ? 'Saving...' : editingId ? 'Save changes' : 'Create availability'}
            </button>
          </form>
        </section>

        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <h3 className="mb-5 text-lg font-semibold text-slate-950">Created availability</h3>

          {loading ? (
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">Loading availability...</div>
          ) : availability.length === 0 ? (
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-6 text-center text-sm text-slate-500">
              No availability has been created yet.
            </div>
          ) : (
            <div className="space-y-4">
              {availability.map((block) => (
                <article key={block.id} className="overflow-hidden rounded-2xl border border-slate-200">
                  <div className="flex flex-col gap-3 bg-blue-50 p-4 md:flex-row md:items-center md:justify-between">
                    <div>
                      <h4 className="font-semibold text-slate-950">
                        {block.date} · {block.startTime}–{block.endTime} · {block.slotCount} slot{block.slotCount === 1 ? '' : 's'}
                      </h4>
                      <p className="mt-1 flex items-center gap-1 text-sm text-slate-500">
                        <MapPin size={15} /> {block.location} · {block.slotDuration} minutes each
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => beginEdit(block)}
                      disabled={!block.canEdit}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                      title={block.canEdit ? 'Edit availability' : 'Availability linked to appointments cannot be edited'}
                    >
                      <Edit3 size={16} /> Edit
                    </button>
                  </div>

                  <div className="grid grid-cols-1 gap-2 p-4 sm:grid-cols-2">
                    {block.slots.map((slot) => (
                      <div key={slot.id} className="flex items-center justify-between rounded-xl border border-slate-100 px-3 py-2 text-sm">
                        <span className="font-medium text-slate-700">{slot.startTime}–{slot.endTime}</span>
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${slot.status === 'Available' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
                          {slot.status}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                    {countAvailableSlots(block)} available slot{countAvailableSlots(block) === 1 ? '' : 's'} in this availability window.
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
