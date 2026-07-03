import { useState } from 'react';
import { Stethoscope, CheckCircle, AlertCircle } from 'lucide-react';
import { useApp } from '../AppContext';
import { postJson } from '../api';

type FieldProps = {
  id: string;
  label: string;
  type?: string;
  placeholder: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
  helper?: string;
  autoComplete?: string;
};

function Field({ id, label, type = 'text', placeholder, value, error, onChange, helper, autoComplete }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-2">{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className={`w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400 ${error ? 'border-red-300' : 'border-slate-200'}`}
      />
      {helper && <p className="text-xs text-slate-400 mt-1">{helper}</p>}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  );
}

export function RegisterPage() {
  const { setCurrentPage } = useApp();
  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [form, setForm] = useState({
    firstName: '', lastName: '', email: '', phone: '', address: '', password: '', confirmPassword: '',
  });

  const update = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: '' }));
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.firstName.trim()) e.firstName = 'First name is required.';
    if (!form.lastName.trim()) e.lastName = 'Last name is required.';
    if (!form.email.match(/^[^@]+@[^@]+\.[^@]+$/)) e.email = 'Please enter a valid email address.';
    if (!form.phone.trim()) e.phone = 'Phone number is required.';
    if (!form.address.trim()) e.address = 'Address is required.';
    if (form.password.length < 8) e.password = 'Password must be at least 8 characters.';
    if (form.password !== form.confirmPassword) e.confirmPassword = 'Passwords do not match.';
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError('');
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setLoading(true);
    try {
      await postJson('/api/register', form);
      setSubmitted(true);
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={32} className="text-green-600" />
          </div>
          <h1 className="font-bold text-slate-900 text-2xl mb-2">Account created</h1>
          <p className="text-slate-500 mb-8">Your patient account has been created. You can now sign in and start using MediQueue.</p>
          <button onClick={() => setCurrentPage('login')} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors">
            Go to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Stethoscope size={22} className="text-white" />
          </div>
          <h1 className="font-bold text-slate-900 text-3xl mb-1">Create patient account</h1>
          <p className="text-slate-500">Register to book appointments and request prescriptions</p>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8">
          {serverError && <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl mb-5"><AlertCircle size={18} className="text-red-600 mt-0.5" /><p className="text-red-700 text-sm">{serverError}</p></div>}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field id="firstName" label="First name" placeholder="Jane" value={form.firstName} error={errors.firstName} onChange={(v) => update('firstName', v)} autoComplete="given-name" />
              <Field id="lastName" label="Last name" placeholder="Smith" value={form.lastName} error={errors.lastName} onChange={(v) => update('lastName', v)} autoComplete="family-name" />
            </div>
            <Field id="email" label="Email address" type="email" placeholder="jane.smith@email.com" value={form.email} error={errors.email} onChange={(v) => update('email', v)} autoComplete="email" />
            <Field id="phone" label="Phone number" type="tel" placeholder="07700 900000" value={form.phone} error={errors.phone} onChange={(v) => update('phone', v)} helper="We may contact you to confirm your appointment." autoComplete="tel" />
            <Field id="address" label="Home address" placeholder="12 High Street, Leicester, LE1 7RH" value={form.address} error={errors.address} onChange={(v) => update('address', v)} autoComplete="street-address" />
            <Field id="password" label="Password" type="password" placeholder="At least 8 characters" value={form.password} error={errors.password} onChange={(v) => update('password', v)} autoComplete="new-password" />
            <Field id="confirmPassword" label="Confirm password" type="password" placeholder="Repeat your password" value={form.confirmPassword} error={errors.confirmPassword} onChange={(v) => update('confirmPassword', v)} autoComplete="new-password" />
            <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors">
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center text-slate-500 text-sm mt-6">
          Already registered?{' '}
          <button onClick={() => setCurrentPage('login')} className="text-blue-600 font-medium hover:text-blue-700">
            Sign in
          </button>
        </p>
        <button onClick={() => setCurrentPage('landing')} className="mt-4 w-full text-center text-slate-500 hover:text-slate-700 text-sm">
          ← Back to home
        </button>
      </div>
    </div>
  );
}
