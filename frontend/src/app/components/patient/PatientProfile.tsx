import { useEffect, useState } from 'react';
import { User, CheckCircle, AlertCircle } from 'lucide-react';
import { apiFetch } from '../../api';

interface ProfileForm {
  firstName: string;
  lastName: string;
  email: string;
  patientReference: string;
  phone: string;
  address: string;
  dateOfBirth: string;
}

export function PatientProfile() {
  const [form, setForm] = useState<ProfileForm>({
    firstName: '',
    lastName: '',
    email: '',
    patientReference: '',
    phone: '',
    address: '',
    dateOfBirth: '',
  });

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadProfile = async () => {
    const data = await apiFetch<{ ok: boolean; profile: ProfileForm }>('/api/patient/profile');
    setForm(data.profile);
    setLoading(false);
  };

  useEffect(() => {
    loadProfile().catch(() => {
      setError('Could not load profile.');
      setLoading(false);
    });
  }, []);

  const updateField = (field: keyof ProfileForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError('');

    try {
      const data = await apiFetch<{ ok: boolean; profile: ProfileForm }>('/api/patient/profile', {
        method: 'PUT',
        body: JSON.stringify(form),
      });

      setForm(data.profile);
      setMessage('Profile updated successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update profile.');
    }
  };

  if (loading) return <div className="text-slate-500">Loading profile...</div>;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-6 md:p-8">
        <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mb-5">
          <User size={26} className="text-blue-600" />
        </div>

        <h2 className="font-bold text-slate-900 text-xl mb-2">My profile</h2>
        <p className="text-slate-500 mb-6">
          Keep your contact details up to date so the GP surgery can manage appointment and prescription communication.
        </p>

        {message && (
          <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-100 rounded-2xl mb-5">
            <CheckCircle size={18} className="text-green-600 mt-0.5" />
            <p className="text-green-700 text-sm">{message}</p>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl mb-5">
            <AlertCircle size={18} className="text-red-600 mt-0.5" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={saveProfile} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">First name</label>
              <input
                value={form.firstName}
                onChange={e => updateField('firstName', e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Last name</label>
              <input
                value={form.lastName}
                onChange={e => updateField('lastName', e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Email</label>
            <input
              value={form.email}
              disabled
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-100 text-slate-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Patient reference</label>
            <input
              value={form.patientReference}
              disabled
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-100 text-slate-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Phone number</label>
            <input
              value={form.phone}
              onChange={e => updateField('phone', e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Date of birth</label>
            <input
              type="date"
              value={form.dateOfBirth}
              onChange={e => updateField('dateOfBirth', e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Address</label>
            <textarea
              value={form.address}
              onChange={e => updateField('address', e.target.value)}
              rows={4}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50"
            />
          </div>

          <button className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors">
            Save profile
          </button>
        </form>
      </div>
    </div>
  );
}
