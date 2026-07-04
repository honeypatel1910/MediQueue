import { useEffect, useState } from 'react';
import { Calendar, FileText, Bell, ChevronRight, Clock, PlusCircle, CreditCard } from 'lucide-react';
import { useApp } from '../../AppContext';
import { apiFetch } from '../../api';
import { StatusBadge } from '../shared/StatusBadge';
import type { Appointment, Prescription, Notification } from '../../types';

export function PatientDashboard() {
  const { currentUser, setCurrentPage, unreadCount } = useApp();
  const [data, setData] = useState<{ appointments: Appointment[]; prescriptions: Prescription[]; notifications: Notification[] }>({ appointments: [], prescriptions: [], notifications: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<{ ok: boolean; appointments: Appointment[]; prescriptions: Prescription[]; notifications: Notification[] }>('/api/patient/dashboard')
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  const upcomingAppt = data.appointments.find(a => a.status === 'Booked' && new Date(a.date) >= new Date(new Date().toDateString()));
  const pendingPrescriptions = data.prescriptions.filter(p => ['Requested', 'Under Review', 'Approved'].includes(p.status));
  const approvedPending = data.prescriptions.find(p => p.status === 'Approved' && p.paymentStatus === 'Pending');
  const readyForCollection = data.prescriptions.find(p => p.status === 'Ready for Collection');
  const recentNotifications = data.notifications.slice(0, 3);

  if (loading) return <div className="text-slate-500">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Hello, {currentUser?.name.split(' ')[0]}</h2>
        <p className="text-slate-500">Here is what needs your attention today.</p>
      </div>

      {approvedPending && (
        <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <CreditCard size={22} className="text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-900">Payment required</p>
              <p className="text-amber-700 text-sm">Your {approvedPending.medicine} prescription has been approved.</p>
            </div>
          </div>
          <button onClick={() => { setCurrentPage('prescription-history'); }} className="px-4 py-2 bg-amber-600 text-white rounded-xl font-medium hover:bg-amber-700 transition-colors">
            Pay now
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Book appointment', desc: 'Choose a time that works for you', icon: <Calendar size={22} className="text-blue-600" />, bg: 'bg-blue-50', page: 'book-appointment' as const },
          { label: 'Request prescription', desc: 'Request a repeat prescription', icon: <PlusCircle size={22} className="text-teal-600" />, bg: 'bg-teal-50', page: 'prescription-request' as const },
          { label: 'View prescriptions', desc: 'Track your prescription status', icon: <FileText size={22} className="text-green-600" />, bg: 'bg-green-50', page: 'prescription-history' as const },
        ].map((a) => (
          <button key={a.label} onClick={() => setCurrentPage(a.page)} className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-md transition-all text-left group">
            <div className={`w-12 h-12 ${a.bg} rounded-xl flex items-center justify-center mb-4`}>{a.icon}</div>
            <p className="font-semibold text-slate-900 group-hover:text-blue-600">{a.label}</p>
            <p className="text-sm text-slate-500 mt-1">{a.desc}</p>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-semibold text-slate-900">Next appointment</h3>
            <button onClick={() => setCurrentPage('appointment-history')} className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">View all <ChevronRight size={14} /></button>
          </div>
          {upcomingAppt ? (
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center"><Calendar size={22} className="text-blue-600" /></div>
                <div>
                  <p className="font-semibold text-slate-900">{upcomingAppt.doctorName}</p>
                  <p className="text-sm text-slate-500">{upcomingAppt.specialisation}</p>
                  <div className="flex items-center gap-2 mt-2 text-sm text-slate-600"><Clock size={14} />{new Date(upcomingAppt.date).toLocaleDateString('en-GB')} at {upcomingAppt.time}</div>
                </div>
              </div>
              <StatusBadge status={upcomingAppt.status} />
            </div>
          ) : (
            <div className="text-center py-8">
              <Calendar size={36} className="text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No upcoming appointments.</p>
              <button onClick={() => setCurrentPage('book-appointment')} className="mt-3 text-blue-600 text-sm font-medium hover:text-blue-700">Book one now</button>
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-semibold text-slate-900">Prescriptions</h3>
            <button onClick={() => setCurrentPage('prescription-history')} className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">View all <ChevronRight size={14} /></button>
          </div>
          {pendingPrescriptions.length || readyForCollection ? (
            <div className="space-y-3">
              {[...pendingPrescriptions, ...(readyForCollection ? [readyForCollection] : [])].slice(0, 4).map(p => (
                <div key={p.id} className="flex items-center justify-between gap-3 p-3 bg-slate-50 rounded-xl">
                  <div>
                    <p className="font-medium text-slate-900 text-sm">{p.medicine}</p>
                    <p className="text-xs text-slate-500">Requested {new Date(p.requestedDate).toLocaleDateString('en-GB')}</p>
                  </div>
                  <StatusBadge status={p.status} />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText size={36} className="text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No active prescriptions.</p>
              <button onClick={() => setCurrentPage('prescription-request')} className="mt-3 text-blue-600 text-sm font-medium hover:text-blue-700">Request prescription</button>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2"><Bell size={18} className="text-blue-600" /> Recent notifications {unreadCount > 0 && <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">{unreadCount} unread</span>}</h3>
          <button onClick={() => setCurrentPage('notifications')} className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">View all <ChevronRight size={14} /></button>
        </div>
        <div className="space-y-3">
          {recentNotifications.length ? recentNotifications.map(n => <div key={n.id} className="p-3 bg-slate-50 rounded-xl"><p className="font-medium text-slate-900 text-sm">{n.title}</p><p className="text-sm text-slate-500">{n.message}</p></div>) : <p className="text-slate-500 text-sm">No notifications yet.</p>}
        </div>
      </div>
    </div>
  );
}
