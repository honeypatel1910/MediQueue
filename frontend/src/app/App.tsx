import { Bell, CalendarDays, FileText, LogOut, Stethoscope, UserRound } from 'lucide-react';
import { AppProvider, useApp } from './AppContext';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { RegisterPage } from './components/RegisterPage';

function DashboardShell() {
  const { currentUser, logout, unreadCount } = useApp();

  if (!currentUser) return <LandingPage />;

  const roleLabel = currentUser.role === 'admin' ? 'Practice Admin' : currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-100 px-6 md:px-12 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Stethoscope size={16} className="text-white" />
          </div>
          <span className="font-semibold text-slate-900 text-lg">MediQueue</span>
        </div>
        <button
          onClick={logout}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-slate-700 hover:bg-slate-100 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </nav>

      <main className="px-6 md:px-12 py-12 max-w-6xl mx-auto">
        <div className="mb-8">
          <p className="text-sm font-semibold text-blue-700 uppercase tracking-[0.2em]">{roleLabel} account</p>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-950 mt-2">Welcome, {currentUser.name}</h1>
          <p className="text-slate-500 mt-3">Your MediQueue account is ready for secure GP appointment and prescription management.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <section className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
            <div className="w-11 h-11 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
              <UserRound className="text-blue-600" size={22} />
            </div>
            <h2 className="font-semibold text-slate-900 mb-1">Profile</h2>
            <p className="text-sm text-slate-500">{currentUser.email}</p>
            {currentUser.patientReference && <p className="text-sm text-slate-500 mt-1">Reference: {currentUser.patientReference}</p>}
          </section>

          <section className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
            <div className="w-11 h-11 bg-green-50 rounded-2xl flex items-center justify-center mb-4">
              <CalendarDays className="text-green-600" size={22} />
            </div>
            <h2 className="font-semibold text-slate-900 mb-1">Appointments</h2>
            <p className="text-sm text-slate-500">Appointment tools will appear inside the full dashboard experience.</p>
          </section>

          <section className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
            <div className="w-11 h-11 bg-purple-50 rounded-2xl flex items-center justify-center mb-4">
              <FileText className="text-purple-600" size={22} />
            </div>
            <h2 className="font-semibold text-slate-900 mb-1">Prescriptions</h2>
            <p className="text-sm text-slate-500">Prescription tools will appear inside the full dashboard experience.</p>
          </section>
        </div>

        <section className="mt-5 bg-white rounded-3xl border border-slate-100 p-6 shadow-sm flex items-start gap-4">
          <div className="w-11 h-11 bg-amber-50 rounded-2xl flex items-center justify-center">
            <Bell className="text-amber-600" size={22} />
          </div>
          <div>
            <h2 className="font-semibold text-slate-900">Notifications</h2>
            <p className="text-sm text-slate-500 mt-1">You have {unreadCount} unread notification{unreadCount === 1 ? '' : 's'}.</p>
          </div>
        </section>
      </main>
    </div>
  );
}

function AppRouter() {
  const { currentPage, currentUser, loadingSession } = useApp();

  if (loadingSession) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600 font-medium">Loading MediQueue...</div>;
  }

  if (!currentUser) {
    if (currentPage === 'login') return <LoginPage />;
    if (currentPage === 'register') return <RegisterPage />;
    return <LandingPage />;
  }

  return <DashboardShell />;
}

export default function App() {
  return (
    <AppProvider>
      <AppRouter />
    </AppProvider>
  );
}
