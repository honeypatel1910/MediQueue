import { Calendar, FileText, Shield, CheckCircle, Clock, Users, Stethoscope, ChevronRight } from 'lucide-react';
import { useApp } from '../AppContext';

export function LandingPage() {
  const { setCurrentPage } = useApp();

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Nav */}
      <nav className="px-6 md:px-12 py-4 flex items-center justify-between border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Stethoscope size={16} className="text-white" />
          </div>
          <span className="font-semibold text-slate-900 text-lg">MediQueue</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setCurrentPage('login')}
            className="px-4 py-2 text-slate-700 font-medium hover:text-blue-600 transition-colors"
          >
            Sign in
          </button>
          <button
            onClick={() => setCurrentPage('register')}
            className="px-4 py-2 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors"
          >
            Register
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 px-6 md:px-12 py-16 md:py-24 max-w-6xl mx-auto w-full">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <CheckCircle size={16} />
            Trusted by local GP surgeries
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 leading-tight">
            Book GP appointments and manage<br className="hidden md:block" />
            <span className="text-blue-600"> prescriptions in one place</span>
          </h1>
          <p className="text-xl text-slate-500 mb-10 max-w-2xl mx-auto leading-relaxed">
            MediQueue makes it easy to book appointments, request prescriptions, and stay up to date with your health — all from your phone or computer.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => setCurrentPage('login')}
              className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-2xl hover:bg-blue-700 transition-colors shadow-sm text-lg"
            >
              Sign in
            </button>
            <button
              onClick={() => setCurrentPage('register')}
              className="px-8 py-4 bg-white text-slate-700 font-semibold rounded-2xl hover:bg-slate-50 transition-colors border border-slate-200 text-lg flex items-center justify-center gap-2"
            >
              Register as patient <ChevronRight size={18} />
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {[
            {
              icon: <Calendar size={28} className="text-blue-600" />,
              bg: 'bg-blue-50',
              title: 'Book appointments online',
              desc: 'Choose a time that works for you. See available slots from your GP or nurse without waiting on hold.',
            },
            {
              icon: <FileText size={28} className="text-teal-600" />,
              bg: 'bg-teal-50',
              title: 'Manage prescriptions',
              desc: 'Request repeat prescriptions and track their progress from approval through to collection.',
            },
            {
              icon: <Shield size={28} className="text-green-600" />,
              bg: 'bg-green-50',
              title: 'Track updates securely',
              desc: 'Get notifications when your prescription is approved, ready to collect, or when appointments change.',
            },
          ].map((f) => (
            <div key={f.title} className="bg-white rounded-2xl p-8 border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
              <div className={`w-14 h-14 ${f.bg} rounded-2xl flex items-center justify-center mb-5`}>
                {f.icon}
              </div>
              <h3 className="font-semibold text-slate-900 mb-2 text-lg">{f.title}</h3>
              <p className="text-slate-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Trust section */}
        <div className="bg-slate-50 rounded-3xl p-8 md:p-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-2 text-center">Built for everyone</h2>
          <p className="text-slate-500 text-center mb-8">Designed to be simple for all users, including those less comfortable with technology.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: <Users size={22} className="text-blue-600" />, label: 'Large, clear text' },
              { icon: <CheckCircle size={22} className="text-green-600" />, label: 'Step-by-step guidance' },
              { icon: <Clock size={22} className="text-amber-600" />, label: 'Available 24 hours' },
              { icon: <Shield size={22} className="text-teal-600" />, label: 'Secure & private' },
            ].map((t) => (
              <div key={t.label} className="flex flex-col items-center gap-2 text-center">
                <div className="w-12 h-12 bg-white rounded-2xl border border-slate-200 flex items-center justify-center">
                  {t.icon}
                </div>
                <span className="text-slate-700 font-medium text-sm">{t.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 px-6 md:px-12 py-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-600 rounded-md flex items-center justify-center">
              <Stethoscope size={12} className="text-white" />
            </div>
            <span className="text-slate-600 font-medium">MediQueue</span>
          </div>
          <p className="text-slate-400 text-sm">Secure GP appointment and prescription management</p>
          <div className="flex gap-6 text-sm text-slate-400">
            <span>Privacy Policy</span>
            <span>Accessibility</span>
            <span>Support</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
