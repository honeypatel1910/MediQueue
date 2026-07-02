import { AppProvider, useApp } from './AppContext';

function AppShell() {
  const { currentUser, loadingSession } = useApp();

  if (loadingSession) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600 font-medium">
        Loading MediQueue...
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
      <section className="max-w-3xl rounded-3xl bg-white p-10 shadow-sm border border-slate-200 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.25em] text-blue-700">MediQueue</p>
        <h1 className="mt-4 text-4xl font-bold text-slate-950">GP appointment and prescription management</h1>
        <p className="mt-4 text-slate-600 leading-7">
          The React frontend foundation is ready and connected to the Flask API session layer.
        </p>
        {currentUser ? (
          <p className="mt-6 rounded-2xl bg-blue-50 px-4 py-3 text-blue-900">
            Signed in as <strong>{currentUser.name}</strong> ({currentUser.role})
          </p>
        ) : (
          <p className="mt-6 rounded-2xl bg-slate-100 px-4 py-3 text-slate-700">
            Public landing, login and registration screens will use this frontend foundation.
          </p>
        )}
      </section>
    </main>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}
