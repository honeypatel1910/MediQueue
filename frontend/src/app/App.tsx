import { Bell, CalendarDays, FileText, ShieldCheck, UserRound } from 'lucide-react';
import { AppProvider, useApp } from './AppContext';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { RegisterPage } from './components/RegisterPage';
import { Layout } from './components/shared/Layout';
import { StatusBadge } from './components/shared/StatusBadge';
import { PatientDashboard } from './components/patient/PatientDashboard';
import { PatientProfile } from './components/patient/PatientProfile';
import { BookAppointment } from './components/patient/BookAppointment';
import { DoctorDashboard } from './components/doctor/DoctorDashboard';
import { NurseDashboard } from './components/nurse/NurseDashboard';
import { Availability } from './components/doctor/Availability';
import type { Page } from './types';

const PAGE_TITLES: Record<Page, string> = {
  landing: 'MediQueue',
  login: 'Sign in',
  register: 'Create account',
  'patient-dashboard': 'Patient Dashboard',
  'book-appointment': 'Book Appointment',
  'appointment-history': 'My Appointments',
  'patient-profile': 'My Profile',
  'prescription-request': 'Request Prescription',
  'prescription-history': 'My Prescriptions',
  'prescription-payment': 'Prescription Payment',
  'doctor-dashboard': 'Doctor Dashboard',
  'doctor-schedule': 'My Schedule',
  'doctor-availability': 'Availability',
  'doctor-prescriptions': 'Prescription Review',
  'nurse-dashboard': 'Nurse Dashboard',
  'nurse-schedule': 'My Schedule',
  'nurse-availability': 'Availability',
  'admin-dashboard': 'Practice Overview',
  'admin-users': 'User Management',
  'admin-appointments': 'Appointment Management',
  'admin-prescriptions': 'Prescription Management',
  'admin-reports': 'Reports',
  'admin-audit': 'Audit Logs',
  notifications: 'Notifications',
};

function roleDisplayName(role?: string) {
  if (role === 'admin') return 'Practice Admin';
  if (!role) return 'User';
  return role.charAt(0).toUpperCase() + role.slice(1);
}

function DashboardOverview() {
  const { currentUser, currentPage, unreadCount } = useApp();
  const title = PAGE_TITLES[currentPage] ?? 'Dashboard';

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">
              {roleDisplayName(currentUser?.role)} account
            </p>
            <h2 className="mt-2 text-3xl font-bold text-slate-950">{title}</h2>
            <p className="mt-3 text-slate-500">
              Welcome, {currentUser?.name}. Use your MediQueue workspace to manage GP appointments, prescriptions and practice activity securely.
            </p>
          </div>
          <StatusBadge status={currentUser?.active === false ? 'Inactive' : 'Active'} />
        </div>
      </section>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50">
            <UserRound className="text-blue-600" size={22} />
          </div>
          <h3 className="mb-1 font-semibold text-slate-900">Profile</h3>
          <p className="text-sm text-slate-500">{currentUser?.email}</p>
          {currentUser?.patientReference && (
            <p className="mt-1 text-sm text-slate-500">Reference: {currentUser.patientReference}</p>
          )}
        </section>

        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-green-50">
            <CalendarDays className="text-green-600" size={22} />
          </div>
          <h3 className="mb-1 font-semibold text-slate-900">Appointments</h3>
          <p className="text-sm text-slate-500">Book, review and manage GP appointments from your dashboard.</p>
        </section>

        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-purple-50">
            <FileText className="text-purple-600" size={22} />
          </div>
          <h3 className="mb-1 font-semibold text-slate-900">Prescriptions</h3>
          <p className="text-sm text-slate-500">Request prescriptions, track review status and manage collection information.</p>
        </section>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50">
            <Bell className="text-amber-600" size={22} />
          </div>
          <h3 className="font-semibold text-slate-900">Notifications</h3>
          <p className="mt-1 text-sm text-slate-500">
            You have {unreadCount} unread notification{unreadCount === 1 ? '' : 's'}.
          </p>
        </section>

        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50">
            <ShieldCheck className="text-teal-600" size={22} />
          </div>
          <h3 className="font-semibold text-slate-900">Secure access</h3>
          <p className="mt-1 text-sm text-slate-500">Your dashboard is protected with role-based access and session authentication.</p>
        </section>
      </div>
    </div>
  );
}

function AppRouter() {
  const { currentPage, currentUser, loadingSession } = useApp();

  if (loadingSession) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 font-medium text-slate-600">Loading MediQueue...</div>;
  }

  if (!currentUser) {
    if (currentPage === 'login') return <LoginPage />;
    if (currentPage === 'register') return <RegisterPage />;
    return <LandingPage />;
  }

  const title = PAGE_TITLES[currentPage] ?? 'Dashboard';

  let content = <DashboardOverview />;
  if (currentPage === 'patient-dashboard') {
    content = <PatientDashboard />;
  } else if (currentPage === 'patient-profile') {
    content = <PatientProfile />;
  } else if (currentPage === 'book-appointment') {
    content = <BookAppointment />;
  } else if (currentPage === 'doctor-dashboard') {
    content = <DoctorDashboard />;
  } else if (currentPage === 'nurse-dashboard') {
    content = <NurseDashboard />;
  } else if (currentPage === 'doctor-availability' || currentPage === 'nurse-availability') {
    content = <Availability />;
  }

  return (
    <Layout title={title}>
      {content}
    </Layout>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppRouter />
    </AppProvider>
  );
}
