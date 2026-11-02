import { useState } from 'react'
import { ExternalLink, Globe2, Loader2, Lock, LockOpen, ShieldQuestion } from 'lucide-react'
import { Badge, PageHeader, Section } from '../components/ui'
import { api } from '../services/api'

export default function SourceCredibility() {
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [r, setR] = useState(null)

  async function submit(e) {
    e.preventDefault()
    if (!value.trim()) { setError(new Error('Enter a URL or domain, e.g. reuters.com')); return }
    setLoading(true); setError(null); setR(null)
    try { setR((await api.source(value.trim())).data) } catch (err) { setError(err) } finally { setLoading(false) }
  }

  return (
    <div>
      <PageHeader title="Source Credibility" subtitle="Look up a publisher: domain, HTTPS certificate, identity and reputation from a configurable source database." />
      <form onSubmit={submit} className="panel mb-6 flex flex-col gap-3 p-5 sm:flex-row" noValidate>
        <input className="input flex-1" value={value} onChange={(e) => setValue(e.target.value)} placeholder="https://www.example.com/article or example.com" aria-label="URL or domain" />
        <button className="btn-primary" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Globe2 className="h-4 w-4" />} Check source</button>
      </form>
      {error && <div className="panel mb-6 border-rose-400/20 p-4 text-sm text-rose-700" role="alert">{error.message}</div>}

      {r && (
        <div className="space-y-5">
          <Section title="Domain information" icon={Globe2}>
            <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
              <div><dt className="label">Domain</dt><dd className="font-mono text-slate-900">{r.domain}</dd></div>
              <div><dt className="label">Registrable domain</dt><dd className="font-mono text-slate-900">{r.registrable_domain}</dd></div>
              <div><dt className="label">HTTPS</dt><dd className="flex items-center gap-1.5">{r.https ? <><Lock className="h-4 w-4 text-emerald-400" /> Valid certificate</> : <><LockOpen className="h-4 w-4 text-amber-400" /> {r.tls?.reason || 'Not confirmed'}</>}</dd></div>
              <div><dt className="label">Publisher identity</dt><dd>{r.publisher_name || 'Not available'} {r.publisher_name_source && <span className="text-xs text-slate-500">({r.publisher_name_source})</span>}</dd></div>
              {r.tls?.available && r.tls.valid && <>
                <div><dt className="label">Certificate issuer</dt><dd>{r.tls.issuer || '—'}</dd></div>
                <div><dt className="label">Certificate expires</dt><dd>{r.tls.expires ? new Date(r.tls.expires).toLocaleDateString() : '—'}</dd></div>
              </>}
            </dl>
          </Section>
          <Section title="Reputation" icon={ShieldQuestion} note={r.disclaimer}>
            <div className="mb-2 flex items-center gap-2"><Badge tone={r.reputation.listed ? (r.reputation.category === 'satire' ? 'warn' : 'info') : 'mute'}>{r.reputation.category.replace('_', ' ')}</Badge>{r.reputation.country && <span className="text-xs text-slate-500">{r.reputation.country}</span>}</div>
            <p className="text-sm text-slate-700">{r.assessment}</p>
            <p className="mt-1 text-xs text-slate-500">{r.reputation.category_description}</p>
          </Section>
        </div>
      )}

      <Section title="Known fact-checking sources" icon={ExternalLink}>
        <p className="mb-3 text-sm text-slate-600">Independent fact-checkers to consult when a claim matters.</p>
        <div className="grid gap-2 sm:grid-cols-2">
          {(r?.fact_checking_references || DEFAULT_REFS).map((f) => (
            <a key={f.url} href={f.url} target="_blank" rel="noopener noreferrer" className="panel panel-hover flex items-center justify-between p-3 text-sm text-slate-800">{f.name}<ExternalLink className="h-3.5 w-3.5 text-slate-500" /></a>
          ))}
        </div>
      </Section>
    </div>
  )
}

// Static link list shown before any lookup; the same list is served by the backend source database.
const DEFAULT_REFS = [
  { name: 'International Fact-Checking Network (Poynter)', url: 'https://www.poynter.org/ifcn/' },
  { name: 'Snopes', url: 'https://www.snopes.com/' },
  { name: 'PolitiFact', url: 'https://www.politifact.com/' },
  { name: 'FactCheck.org', url: 'https://www.factcheck.org/' },
  { name: 'Full Fact', url: 'https://fullfact.org/' },
  { name: 'Alt News', url: 'https://www.altnews.in/' },
]
