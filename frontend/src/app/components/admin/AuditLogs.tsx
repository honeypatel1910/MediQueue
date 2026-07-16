import { useEffect, useState } from 'react';
import { Search, Shield } from 'lucide-react';
import { apiFetch } from '../../api';

interface AuditLog { id: string; action: string; user: string; role: string; datetime: string; entity: string; description: string; }

export function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('All');
  const [dateFilter, setDateFilter] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => { apiFetch<{ ok: boolean; auditLogs: AuditLog[] }>('/api/audit-logs').then(d => setLogs(d.auditLogs)).finally(() => setLoading(false)); }, []);
  const actions = ['All', ...Array.from(new Set(logs.map(l => l.action)))];
  const filtered = logs.filter(l => { const q = search.toLowerCase(); return (!q || l.action.toLowerCase().includes(q) || l.user.toLowerCase().includes(q) || l.description.toLowerCase().includes(q)) && (actionFilter === 'All' || l.action === actionFilter) && (!dateFilter || l.datetime.startsWith(dateFilter)); });
  if (loading) return <div className="text-slate-500">Loading audit logs...</div>;
  return <div className="space-y-6"><div className="flex flex-col md:flex-row gap-3"><div className="relative flex-1"><Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search audit logs" className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" /></div><select value={actionFilter} onChange={e => setActionFilter(e.target.value)} className="px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">{actions.map(a => <option key={a}>{a}</option>)}</select><input type="date" value={dateFilter} onChange={e => setDateFilter(e.target.value)} className="px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white" /></div><div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden"><div className="overflow-x-auto"><table className="w-full text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th className="text-left p-4">Action</th><th className="text-left p-4">User</th><th className="text-left p-4">Entity</th><th className="text-left p-4">Date/time</th><th className="text-left p-4">Details</th></tr></thead><tbody>{filtered.map(l => <tr key={l.id} className="border-t border-slate-100"><td className="p-4 font-medium text-slate-900">{l.action}</td><td className="p-4 text-slate-600">{l.user}<br /><span className="text-xs text-slate-400">{l.role}</span></td><td className="p-4 text-slate-500">{l.entity}</td><td className="p-4 text-slate-500">{new Date(l.datetime).toLocaleString('en-GB')}</td><td className="p-4 text-slate-500 max-w-sm">{l.description}</td></tr>)}</tbody></table></div>{filtered.length === 0 && <div className="p-12 text-center"><Shield size={40} className="text-slate-300 mx-auto mb-4" /><p className="text-slate-500">No audit logs found.</p></div>}</div></div>;
}
