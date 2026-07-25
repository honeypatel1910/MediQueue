import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CalendarDays, CheckCircle2, Clock, Filter, MapPin, Search, Stethoscope, X } from 'lucide-react';
import { apiFetch } from '../../api';
import type { Appointment, AvailabilitySlot } from '../../types';

interface AvailableAppointmentsResponse {
  ok: boolean;
  slots: AvailabilitySlot[];
  staff: Array<{
    id: string;
    name: string;
    role: 'Doctor' | 'Nurse' | string;
    specialisation: string;
  }>;
}

interface BookAppointmentResponse {
  ok: boolean;
  appointment: Appointment;
  message?: string;
}

interface BookingPopup {
  variant: 'success' | 'approval';
  title: string;
  message: string;
  detail: string;
}

function tomorrowDate() {
  const value = new Date();
  value.setDate(value.getDate() + 1);
  return value.toISOString().slice(0, 10);
}

export function BookAppointment() {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [staff, setStaff] = useState<AvailableAppointmentsResponse['staff']>([]);
  const [date, setDate] = useState(tomorrowDate());
  const [staffId, setStaffId] = useState('');
  const [role, setRole] = useState('');
  const [reason, setReason] = useState('');
  const [selectedSlotId, setSelectedSlotId] = useState('');
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [bookingPopup, setBookingPopup] = useState<BookingPopup | null>(null);

  const selectedSlot = useMemo(() => slots.find((slot) => slot.id === selectedSlotId) || null, [slots, selectedSlotId]);

  const loadSlots = async ({ clearFeedback = true }: { clearFeedback?: boolean } = {}) => {
    setError('');
    if (clearFeedback) {
      setMessage('');
    }
    const params = new URLSearchParams();
    if (date) params.set('date', date);
    if (staffId) params.set('staffId', staffId);
    if (role) params.set('role', role);

    const data = await apiFetch<AvailableAppointmentsResponse>(`/api/appointments/available?${params.toString()}`);
    setSlots(data.slots || []);
    setStaff(data.staff || []);
    setSelectedSlotId('');
  };

  useEffect(() => {
    loadSlots()
      .catch((err) => setError(err.message || 'Available appointments could not be loaded.'))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    setBookingPopup(null);
    setLoading(true);
    await loadSlots()
      .catch((err) => setError(err.message || 'Available appointments could not be loaded.'))
      .finally(() => setLoading(false));
  };

  const bookSelectedSlot = async () => {
    if (!selectedSlotId) {
      setError('Please choose an appointment slot.');
      return;
    }

    setBooking(true);
    setError('');
    setMessage('');
    setBookingPopup(null);

    try {
      const data = await apiFetch<BookAppointmentResponse>('/api/appointments/book', {
        method: 'POST',
        body: JSON.stringify({ slotId: selectedSlotId, reason }),
      });

      const appointmentSummary = `${new Date(data.appointment.date).toLocaleDateString('en-GB')} at ${data.appointment.time}`;

      if (data.appointment.status === 'Pending Approval') {
        const approvalMessage =
          data.message ||
          `Your extra appointment request with ${data.appointment.doctorName} has been sent for approval. Please wait for staff approval before attending.`;
        setMessage(approvalMessage);
        setBookingPopup({
          variant: 'approval',
          title: 'Waiting for staff approval',
          message: approvalMessage,
          detail: `${data.appointment.doctorName} · ${appointmentSummary}`,
        });
      } else {
        const bookedMessage =
          data.message ||
          `Appointment confirmed with ${data.appointment.doctorName} on ${appointmentSummary}.`;
        setMessage(bookedMessage);
        setBookingPopup({
          variant: 'success',
          title: 'Appointment confirmed',
          message: bookedMessage,
          detail: `${data.appointment.doctorName} · ${appointmentSummary}`,
        });
      }

      setReason('');
      await loadSlots({ clearFeedback: false });
    } catch (err) {
      setBookingPopup(null);
      setError(err instanceof Error ? err.message : 'Appointment could not be booked.');
    } finally {
      setBooking(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm md:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Appointments</p>
        <h2 className="mt-2 text-3xl font-bold text-slate-950">Book a GP appointment</h2>
        <p className="mt-3 text-slate-500">
          Search available clinical slots, choose a suitable time and confirm your appointment securely.
        </p>
      </section>

      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
        <form onSubmit={handleSearch} className="grid grid-cols-1 gap-4 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Appointment date</span>
            <input
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Staff member</span>
            <select
              value={staffId}
              onChange={(event) => setStaffId(event.target.value)}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            >
              <option value="">Any staff member</option>
              {staff.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} · {item.role}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Clinical role</span>
            <select
              value={role}
              onChange={(event) => setRole(event.target.value)}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
            >
              <option value="">Doctor or nurse</option>
              <option value="doctor">Doctor</option>
              <option value="nurse">Nurse</option>
            </select>
          </label>

          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            <Search size={18} /> Search
          </button>
        </form>
      </section>

      {error && (
        <div className="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
          <AlertCircle size={18} className="mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {message && (
        <div className={`flex items-start gap-3 rounded-2xl border p-4 text-sm ${message.toLowerCase().includes('approval') ? 'border-amber-100 bg-amber-50 text-amber-700' : 'border-green-100 bg-green-50 text-green-700'}`}>
          <CheckCircle2 size={18} className="mt-0.5" />
          <span>{message}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_380px]">
        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-950">Available slots</h3>
              <p className="text-sm text-slate-500">Choose one open appointment slot.</p>
            </div>
            <div className="flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1 text-sm font-medium text-slate-600">
              <Filter size={15} /> {slots.length} slot{slots.length === 1 ? '' : 's'}
            </div>
          </div>

          {loading ? (
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-6 text-center text-sm text-slate-500">Loading appointment slots...</div>
          ) : slots.length === 0 ? (
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-8 text-center">
              <CalendarDays size={40} className="mx-auto mb-3 text-slate-300" />
              <p className="font-medium text-slate-700">No available slots found.</p>
              <p className="mt-1 text-sm text-slate-500">Try another date or staff filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {slots.map((slot) => (
                <button
                  key={slot.id}
                  onClick={() => setSelectedSlotId(slot.id)}
                  className={`rounded-2xl border p-4 text-left transition-all ${
                    selectedSlotId === slot.id
                      ? 'border-blue-500 bg-blue-50 shadow-sm ring-4 ring-blue-100'
                      : 'border-slate-100 bg-white hover:border-blue-200 hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="flex items-center gap-2 font-semibold text-slate-950">
                        <Clock size={17} className="text-blue-600" /> {slot.time}
                      </p>
                      <p className="mt-1 text-sm text-slate-500">{new Date(slot.date).toLocaleDateString('en-GB')} · {slot.duration} minutes</p>
                    </div>
                    <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-700">Available</span>
                  </div>

                  <div className="mt-4 space-y-1 text-sm text-slate-600">
                    <p className="flex items-center gap-2"><Stethoscope size={15} /> {slot.staffName}</p>
                    <p className="flex items-center gap-2"><MapPin size={15} /> {slot.specialisation || 'General Practice'}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <aside className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-950">Confirm appointment</h3>
          {selectedSlot ? (
            <div className="mt-5 space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-950">{selectedSlot.staffName}</p>
                <p className="mt-1 text-sm text-slate-500">{selectedSlot.role} · {selectedSlot.specialisation}</p>
                <p className="mt-3 text-sm font-medium text-slate-700">
                  {new Date(selectedSlot.date).toLocaleDateString('en-GB')} at {selectedSlot.time}
                </p>
              </div>

              <label className="block">
                <span className="mb-1 block text-sm font-medium text-slate-700">Reason for visit</span>
                <textarea
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  rows={5}
                  placeholder="Briefly describe the reason for your appointment"
                  className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>

              <button
                onClick={bookSelectedSlot}
                disabled={booking}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {booking ? 'Booking...' : 'Book appointment'}
              </button>
            </div>
          ) : (
            <div className="mt-5 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
              Select an available slot to continue.
            </div>
          )}
        </aside>
      </div>

      {bookingPopup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-2xl ${
                  bookingPopup.variant === 'approval' ? 'bg-amber-50' : 'bg-green-50'
                }`}
              >
                {bookingPopup.variant === 'approval' ? (
                  <AlertCircle size={24} className="text-amber-600" />
                ) : (
                  <CheckCircle2 size={24} className="text-green-600" />
                )}
              </div>
              <button
                type="button"
                onClick={() => setBookingPopup(null)}
                className="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
                aria-label="Close appointment confirmation"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-5">
              <h3 className="text-xl font-bold text-slate-950">{bookingPopup.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">{bookingPopup.message}</p>
              <div
                className={`mt-4 rounded-2xl px-4 py-3 text-sm font-medium ${
                  bookingPopup.variant === 'approval'
                    ? 'bg-amber-50 text-amber-800'
                    : 'bg-green-50 text-green-800'
                }`}
              >
                {bookingPopup.detail}
              </div>
            </div>

            <button
              type="button"
              onClick={() => setBookingPopup(null)}
              className={`mt-6 w-full rounded-xl px-4 py-3 text-sm font-semibold text-white transition ${
                bookingPopup.variant === 'approval' ? 'bg-amber-600 hover:bg-amber-700' : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {bookingPopup.variant === 'approval' ? 'Okay, I will wait' : 'Done'}
            </button>
          </div>
        </div>
      )}

    </div>
  );
}