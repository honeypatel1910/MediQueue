import { useState } from 'react';
import { Eye, EyeOff, Stethoscope, AlertCircle } from 'lucide-react';
import { useApp } from '../AppContext';

export function LoginPage() {
  const { login, setCurrentPage, setPendingVerificationEmail } = useApp();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'We could not sign you in.';
      if (message.toLowerCase().includes('verify')) {
        setPendingVerificationEmail(email);
      }
      setError(message);
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
          <h1 className="font-bold text-slate-900 text-3xl mb-1">Welcome back</h1>
          <p className="text-slate-500">Sign in to your MediQueue account</p>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="space-y-3 rounded-2xl border border-red-100 bg-red-50 p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle size={18} className="text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
                {error.toLowerCase().includes('verify') && (
                  <button
                    type="button"
                    onClick={() => {
                      setPendingVerificationEmail(email);
                      setCurrentPage('verify-email');
                    }}
                    className="w-full rounded-xl bg-white px-4 py-2 text-sm font-semibold text-red-700 border border-red-100 hover:bg-red-100 transition-colors"
                  >
                    Verify email OTP
                  </button>
                )}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                autoComplete="email"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-400 bg-slate-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2" htmlFor="password">Password</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                  className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-400 bg-slate-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-60 transition-colors"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-slate-500 text-sm mt-6">
          New patient?{' '}
          <button onClick={() => setCurrentPage('register')} className="text-blue-600 font-medium hover:text-blue-700">
            Create an account
          </button>
        </p>
        <button onClick={() => setCurrentPage('landing')} className="mt-4 w-full text-center text-slate-500 hover:text-slate-700 text-sm">
          ← Back to home
        </button>
      </div>
    </div>
  );
}
