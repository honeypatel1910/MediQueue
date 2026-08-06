import { useState } from 'react';
import { AlertCircle, CheckCircle, KeyRound, Mail, ShieldCheck, Stethoscope } from 'lucide-react';
import { useApp } from '../AppContext';
import { postJson } from '../api';

type ApiMessageResponse = {
  ok: boolean;
  message: string;
  emailSent?: boolean;
};

type Step = 'request' | 'verify' | 'reset' | 'complete';

export function ForgotPasswordPage() {
  const { setCurrentPage } = useApp();
  const [step, setStep] = useState<Step>('request');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const normalisedEmail = email.trim().toLowerCase();

  const resetStatus = () => {
    setError('');
    setMessage('');
  };

  const requestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    resetStatus();
    if (!normalisedEmail) {
      setError('Registered email address is required.');
      return;
    }

    setLoading(true);
    try {
      const data = await postJson<ApiMessageResponse>('/api/password-reset/request', { email: normalisedEmail });
      setMessage(
        data.emailSent === false
          ? `${data.message} If you are testing locally, check MAIL_SUPPRESS_SEND and SMTP settings in .env.`
          : data.message,
      );
      setStep('verify');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not request password reset OTP.');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    resetStatus();
    if (!normalisedEmail || !otp.trim()) {
      setError('Email address and OTP are required.');
      return;
    }

    setLoading(true);
    try {
      const data = await postJson<ApiMessageResponse>('/api/password-reset/verify', {
        email: normalisedEmail,
        otp: otp.trim(),
      });
      setMessage(data.message || 'OTP verified. You can now set a new password.');
      setStep('reset');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OTP verification failed.');
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    resetStatus();
    if (password.length < 8) {
      setError('New password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setError('New password and retype password do not match.');
      return;
    }

    setLoading(true);
    try {
      const data = await postJson<ApiMessageResponse>('/api/password-reset/confirm', {
        email: normalisedEmail,
        password,
        confirmPassword,
      });
      setPassword('');
      setConfirmPassword('');
      setMessage(data.message || 'Password reset successfully. You can now sign in.');
      setStep('complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Password reset failed.');
    } finally {
      setLoading(false);
    }
  };

  const resendOtp = async () => {
    resetStatus();
    if (!normalisedEmail) {
      setError('Enter your registered email address first.');
      return;
    }
    setLoading(true);
    try {
      const data = await postJson<ApiMessageResponse>('/api/password-reset/request', { email: normalisedEmail });
      setMessage(data.message || 'A new reset OTP has been sent.');
      setStep('verify');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not resend password reset OTP.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Stethoscope size={22} className="text-white" />
          </div>
          <h1 className="font-bold text-slate-900 text-3xl mb-1">Reset password</h1>
          <p className="text-slate-500">Verify your registered email with OTP before setting a new password.</p>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8">
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl mb-5">
              <AlertCircle size={18} className="text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {message && step !== 'complete' && (
            <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-100 rounded-2xl mb-5">
              <Mail size={18} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-blue-700 text-sm">{message}</p>
            </div>
          )}

          {step === 'request' && (
            <form onSubmit={requestOtp} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="reset-email">Registered email address</label>
                <div className="relative">
                  <input
                    id="reset-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    required
                    autoComplete="email"
                    className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400"
                  />
                  <Mail className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                </div>
              </div>
              <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors">
                {loading ? 'Sending OTP...' : 'Send reset OTP'}
              </button>
            </form>
          )}

          {step === 'verify' && (
            <form onSubmit={verifyOtp} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="verify-reset-email">Email address</label>
                <input
                  id="verify-reset-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="reset-otp">6-digit OTP</label>
                <div className="relative">
                  <input
                    id="reset-otp"
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
              </div>
              <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors">
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>
              <button type="button" onClick={resendOtp} disabled={loading} className="w-full py-3 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 disabled:opacity-60 transition-colors">
                Resend OTP
              </button>
            </form>
          )}

          {step === 'reset' && (
            <form onSubmit={resetPassword} className="space-y-5">
              <div className="flex items-start gap-3 rounded-2xl border border-green-100 bg-green-50 p-4">
                <ShieldCheck size={18} className="mt-0.5 flex-shrink-0 text-green-600" />
                <p className="text-sm text-green-700">OTP verified. Enter and retype your new password.</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="new-password">New password</label>
                <input
                  id="new-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  required
                  autoComplete="new-password"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="confirm-new-password">Retype new password</label>
                <input
                  id="confirm-new-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat new password"
                  required
                  autoComplete="new-password"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50 text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <button type="submit" disabled={loading} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors">
                {loading ? 'Resetting password...' : 'Reset password'}
              </button>
            </form>
          )}

          {step === 'complete' && (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle size={32} className="text-green-600" />
              </div>
              <h2 className="font-bold text-slate-900 text-2xl mb-2">Password reset complete</h2>
              <p className="text-slate-500 mb-8">{message || 'You can now sign in with your new password.'}</p>
              <button onClick={() => setCurrentPage('login')} className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors">
                Go to sign in
              </button>
            </div>
          )}
        </div>

        {step !== 'complete' && (
          <p className="text-center text-slate-500 text-sm mt-6">
            Remembered your password?{' '}
            <button onClick={() => setCurrentPage('login')} className="text-blue-600 font-medium hover:text-blue-700">
              Sign in
            </button>
          </p>
        )}
        <button onClick={() => setCurrentPage('landing')} className="mt-4 w-full text-center text-slate-500 hover:text-slate-700 text-sm">
          ← Back to home
        </button>
      </div>
    </div>
  );
}
