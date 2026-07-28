import { useState } from 'react';
import { AlertCircle, CheckCircle, KeyRound, Mail, Stethoscope } from 'lucide-react';
import { useApp } from '../AppContext';
import { postJson } from '../api';

type VerifyResponse = {
  ok: boolean;
  message: string;
};

type ResendResponse = {
  ok: boolean;
  message: string;
  emailSent: boolean;
};

export function VerifyEmailPage() {
  const { pendingVerificationEmail, setPendingVerificationEmail, setCurrentPage } = useApp();
  const [email, setEmail] = useState(pendingVerificationEmail);
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [verified, setVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  const normalisedEmail = email.trim().toLowerCase();

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!normalisedEmail) {
      setError('Email address is required.');
      return;
    }
    if (!otp.trim()) {
      setError('OTP code is required.');
      return;
    }

    setLoading(true);
    try {
      const data = await postJson<VerifyResponse>('/api/verify-email', {
        email: normalisedEmail,
        otp: otp.trim(),
      });
      setPendingVerificationEmail('');
      setVerified(true);
      setMessage(data.message || 'Email verified successfully. You can now sign in.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setMessage('');

    if (!normalisedEmail) {
      setError('Enter your registered email address first.');
      return;
    }

    setResending(true);
    try {
      const data = await postJson<ResendResponse>('/api/resend-email-otp', { email: normalisedEmail });
      setPendingVerificationEmail(normalisedEmail);
      setMessage(
        data.emailSent
          ? data.message
          : 'A new OTP was generated, but email sending is currently suppressed or not configured. Check SMTP settings in .env.',
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not resend OTP.');
    } finally {
      setResending(false);
    }
  };

  if (verified) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle size={32} className="text-green-600" />
          </div>
          <h1 className="font-bold text-slate-900 text-2xl mb-2">Email verified</h1>
          <p className="text-slate-500 mb-8">{message}</p>
          <button onClick={() => setCurrentPage('login')} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors">
            Go to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Stethoscope size={22} className="text-white" />
          </div>
          <h1 className="font-bold text-slate-900 text-3xl mb-1">Verify your email</h1>
          <p className="text-slate-500">Enter the OTP sent to your registered email address.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8">
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl mb-5">
              <AlertCircle size={18} className="text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {message && (
            <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-100 rounded-2xl mb-5">
              <Mail size={18} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-blue-700 text-sm">{message}</p>
            </div>
          )}

          <form onSubmit={handleVerify} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="verify-email">Email address</label>
              <input
                id="verify-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                autoComplete="email"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="otp">6-digit OTP</label>
              <div className="relative">
                <input
                  id="otp"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="123456"
                  required
                  className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400 tracking-[0.4em] font-semibold"
                />
                <KeyRound className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              </div>
              <p className="text-xs text-slate-400 mt-1">The OTP expires after 10 minutes.</p>
            </div>

            <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors">
              {loading ? 'Verifying...' : 'Verify email'}
            </button>
          </form>

          <button
            type="button"
            onClick={handleResend}
            disabled={resending}
            className="mt-4 w-full py-3 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 disabled:opacity-60 transition-colors"
          >
            {resending ? 'Sending new OTP...' : 'Resend OTP'}
          </button>
        </div>

        <p className="text-center text-slate-500 text-sm mt-6">
          Already verified?{' '}
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
