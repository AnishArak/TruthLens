import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-slate-600" role="status">
      <Loader2 className="h-5 w-5 animate-spin text-accent" /> <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="panel flex flex-col items-center gap-3 p-8 text-center" role="alert">
      <AlertTriangle className="h-6 w-6 text-amber-400" />
      <p className="max-w-md text-sm text-slate-700">{error?.message || 'Something went wrong.'}</p>
      {onRetry && (
        <button className="btn-ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint, action }) {
  return (
    <div className="panel flex flex-col items-center gap-2 p-10 text-center">
      <Inbox className="h-7 w-7 text-slate-500" />
      <h3 className="font-semibold text-slate-900">{title}</h3>
      {hint && <p className="max-w-md text-sm text-slate-600">{hint}</p>}
      {action}
    </div>
  )
}

const TONES = {
  real: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-700',
  fake: 'border-rose-400/30 bg-rose-400/10 text-rose-700',
  warn: 'border-amber-400/30 bg-amber-400/10 text-amber-700',
  info: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-700',
  mute: 'border-slate-200 bg-slate-100 text-slate-700',
}

export function Badge({ tone = 'mute', children, className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${TONES[tone]} ${className}`}>
      {children}
    </span>
  )
}

export const predictionTone = (p) => (p === 'FAKE' ? 'fake' : 'real')

export function evidenceTone(label = '') {
  if (label.startsWith('Supporting')) return 'real'
  if (label.startsWith('Contradicting')) return 'fake'
  if (label.startsWith('Mixed')) return 'warn'
  if (label.startsWith('Insufficient')) return 'mute'
  return 'info'
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-slate-600">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

export function Section({ title, icon: Icon, children, note }) {
  return (
    <section className="panel p-5 sm:p-6">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-700">
        {Icon && <Icon className="h-4 w-4 text-accent" />} {title}
      </h2>
      {children}
      {note && <p className="mt-4 border-t border-slate-100 pt-3 text-xs leading-relaxed text-slate-500">{note}</p>}
    </section>
  )
}

export const pct = (v, d = 1) => (typeof v === 'number' ? `${(v * 100).toFixed(d)}%` : '—')
export const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—')

export function Logo({ className = '' }) {
  return (
    <span className={`inline-flex items-center gap-2.5 font-bold tracking-tight text-slate-900 ${className}`}>
      <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#ffffff" stroke="rgba(8,145,178,0.4)" />
        <circle cx="15" cy="15" r="7" fill="none" stroke="#0891b2" strokeWidth="2.5" />
        <path d="M20.5 20.5 26 26" stroke="#0891b2" strokeWidth="2.5" strokeLinecap="round" />
        <path d="m12 15 2.2 2.2L18.5 12.8" fill="none" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      Truth<span className="text-accent">Lens</span>
    </span>
  )
}
