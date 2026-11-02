import { useState } from 'react'
import { NavLink, Outlet, Link } from 'react-router-dom'
import { BarChart3, BookOpen, Cpu, Globe2, History, LayoutDashboard, Menu, ScanSearch, X } from 'lucide-react'
import { Logo } from '../components/ui'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'

const NAV = [
  { to: '/app', end: true, label: 'Dashboard', icon: LayoutDashboard },
  { to: '/app/analyze', label: 'News Analyzer', icon: ScanSearch },
  { to: '/app/source', label: 'Source Credibility', icon: Globe2 },
  { to: '/app/history', label: 'Analysis History', icon: History },
  { to: '/app/models', label: 'Model Performance', icon: Cpu },
  { to: '/app/about', label: 'About Project', icon: BookOpen },
]

function StatusDot({ ok, label }) {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-600">
      <span className={`h-2 w-2 rounded-full ${ok ? 'bg-emerald-400' : 'bg-amber-400'}`} /> {label}
    </div>
  )
}

function Sidebar({ onNavigate }) {
  const { data, error } = useFetch(api.health, [])
  return (
    <div className="flex h-full flex-col gap-6 p-5">
      <Link to="/" onClick={onNavigate}>
        <Logo className="text-lg" />
      </Link>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ to, end, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive ? 'bg-accent/10 text-accent' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`
            }
          >
            <Icon className="h-4 w-4" /> {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto space-y-2 rounded-xl border border-slate-100 bg-slate-50 p-3">
        <p className="label">System status</p>
        {error ? (
          <StatusDot ok={false} label="Backend offline" />
        ) : data ? (
          <>
            <StatusDot ok label="Backend online" />
            <StatusDot ok={data.model_trained} label={data.model_trained ? 'Model trained' : 'Model not trained'} />
            <StatusDot ok={data.database.available} label={data.database.available ? 'MongoDB connected' : 'MongoDB offline'} />
            <StatusDot ok={data.evidence_provider.configured} label={data.evidence_provider.configured ? `Search: ${data.evidence_provider.name}` : 'Search not configured'} />
          </>
        ) : (
          <StatusDot ok={false} label="Checking…" />
        )}
      </div>
    </div>
  )
}

export default function AppLayout() {
  const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen lg:pl-64">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-slate-100 bg-white/90 backdrop-blur lg:block">
        <Sidebar />
      </aside>

      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-100 bg-white/80 px-4 py-3 backdrop-blur lg:hidden">
        <Logo />
        <button className="btn-ghost !p-2" onClick={() => setOpen(true)} aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white">
            <button className="absolute right-3 top-3 text-slate-600" onClick={() => setOpen(false)} aria-label="Close menu">
              <X className="h-5 w-5" />
            </button>
            <Sidebar onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
        <Outlet />
      </main>
    </div>
  )
}
