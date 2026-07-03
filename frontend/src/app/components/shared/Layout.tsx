import { useState } from 'react';
import {
  LayoutDashboard,
  Calendar,
  FileText,
  PlusCircle,
  Bell,
  LogOut,
  ClipboardList,
  Users,
  BarChart2,
  Shield,
  Menu,
  Clock,
  Stethoscope,
  UserCircle,
} from 'lucide-react';
import { useApp } from '../../AppContext';
import type { Page } from '../../types';

interface NavItem {
  label: string;
  page: Page;
  icon: React.ReactNode;
}

function getNavItems(role: string): NavItem[] {
  if (role === 'patient') {
    return [
      { label: 'Dashboard', page: 'patient-dashboard', icon: <LayoutDashboard size={20} /> },
      { label: 'Book Appointment', page: 'book-appointment', icon: <Calendar size={20} /> },
      { label: 'My Appointments', page: 'appointment-history', icon: <ClipboardList size={20} /> },
      { label: 'My Profile', page: 'patient-profile', icon: <UserCircle size={20} /> },
      { label: 'Request Prescription', page: 'prescription-request', icon: <PlusCircle size={20} /> },
      { label: 'My Prescriptions', page: 'prescription-history', icon: <FileText size={20} /> },
    ];
  }

  if (role === 'doctor') {
    return [
      { label: 'Dashboard', page: 'doctor-dashboard', icon: <LayoutDashboard size={20} /> },
      { label: 'My Schedule', page: 'doctor-schedule', icon: <Calendar size={20} /> },
      { label: 'Availability', page: 'doctor-availability', icon: <Clock size={20} /> },
      { label: 'Prescriptions', page: 'doctor-prescriptions', icon: <FileText size={20} /> },
    ];
  }

  if (role === 'nurse') {
    return [
      { label: 'Dashboard', page: 'nurse-dashboard', icon: <LayoutDashboard size={20} /> },
      { label: 'My Schedule', page: 'nurse-schedule', icon: <Calendar size={20} /> },
      { label: 'Availability', page: 'nurse-availability', icon: <Clock size={20} /> },
    ];
  }

  return [
    { label: 'Dashboard', page: 'admin-dashboard', icon: <LayoutDashboard size={20} /> },
    { label: 'Users', page: 'admin-users', icon: <Users size={20} /> },
    { label: 'Appointments', page: 'admin-appointments', icon: <Calendar size={20} /> },
    { label: 'Prescriptions', page: 'admin-prescriptions', icon: <FileText size={20} /> },
    { label: 'Reports', page: 'admin-reports', icon: <BarChart2 size={20} /> },
    { label: 'Audit Logs', page: 'admin-audit', icon: <Shield size={20} /> },
  ];
}

const roleLabel: Record<string, string> = {
  patient: 'Patient',
  doctor: 'Doctor',
  nurse: 'Nurse',
  admin: 'Practice Admin',
};

const roleBg: Record<string, string> = {
  patient: 'bg-blue-100 text-blue-700',
  doctor: 'bg-teal-100 text-teal-700',
  nurse: 'bg-purple-100 text-purple-700',
  admin: 'bg-amber-100 text-amber-700',
};

export function Layout({ children, title }: { children: React.ReactNode; title: string }) {
  const { currentUser, currentPage, setCurrentPage, logout, unreadCount } = useApp();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navItems = getNavItems(currentUser?.role ?? '');
  const initials = currentUser?.name
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const SidebarContent = () => (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-100 p-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Stethoscope size={16} className="text-white" />
          </div>
          <span className="text-lg font-semibold text-slate-800">MediQueue</span>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {navItems.map((item) => (
          <button
            key={item.page}
            onClick={() => {
              setCurrentPage(item.page);
              setSidebarOpen(false);
            }}
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-all duration-150 ${
              currentPage === item.page
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            {item.icon}
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="border-t border-slate-100 p-4">
        <div className="mb-2 flex items-center gap-3 px-3 py-2">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-blue-100">
            <span className="text-sm font-semibold text-blue-700">{initials}</span>
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-800">{currentUser?.name}</p>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${roleBg[currentUser?.role ?? 'patient']}`}>
              {roleLabel[currentUser?.role ?? 'patient']}
            </span>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600"
        >
          <LogOut size={18} />
          <span className="text-sm font-medium">Sign out</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="sticky top-0 hidden h-screen w-64 flex-shrink-0 flex-col border-r border-slate-100 bg-white md:flex">
        <SidebarContent />
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
          <aside className="relative h-full w-72 bg-white shadow-xl">
            <SidebarContent />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex items-center justify-between border-b border-slate-100 bg-white px-4 py-4 md:px-8">
          <div className="flex items-center gap-4">
            <button
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </button>
            <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
          </div>
          <button
            onClick={() => setCurrentPage('notifications')}
            className="relative rounded-xl p-2 text-slate-600 transition-colors hover:bg-slate-100"
            aria-label="Notifications"
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs font-medium text-white">
                {unreadCount}
              </span>
            )}
          </button>
        </header>

        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
