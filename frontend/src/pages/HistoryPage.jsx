import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Eye, Search, Trash2 } from 'lucide-react'
import AnalysisResult from '../components/AnalysisResult'
import { Badge, EmptyState, ErrorState, PageHeader, Spinner, evidenceTone, fmtDate, pct, predictionTone } from '../components/ui'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'

function Detail({ id }) {
  const navigate = useNavigate()
  const { data, error, loading, reload } = useFetch(() => api.historyItem(id), [id])
  const [deleting, setDeleting] = useState(false)

  async function remove() {
    if (!window.confirm('Delete this analysis permanently?')) return
    setDeleting(true)
    try { await api.deleteHistory(id); navigate('/app/history') } catch (e) { alert(e.message); setDeleting(false) }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorState error={error} onRetry={reload} />
  return (
    <div>
      <Link to="/app/history" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900"><ArrowLeft className="h-4 w-4" /> Back to history</Link>
      <PageHeader title={data.headline} subtitle={`Analysed ${fmtDate(data.created_at)}`}>
        <button className="btn-danger" onClick={remove} disabled={deleting}><Trash2 className="h-4 w-4" /> Delete</button>
      </PageHeader>
      {data.full_result ? <AnalysisResult result={{ ...data.full_result, created_at: data.created_at }} /> : <EmptyState title="No stored detail" hint="This record has no full result." />}
    </div>
  )
}

function List() {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [prediction, setPrediction] = useState('')
  const [status, setStatus] = useState('')
  const [busyId, setBusyId] = useState(null)

  useEffect(() => { const t = setTimeout(() => setDebounced(search), 300); return () => clearTimeout(t) }, [search])
  const fetcher = useCallback(() => api.history({ search: debounced, prediction, status }), [debounced, prediction, status])
  const { data, error, loading, reload } = useFetch(fetcher, [fetcher])

  async function remove(id) {
    if (!window.confirm('Delete this analysis permanently?')) return
    setBusyId(id)
    try { await api.deleteHistory(id); reload() } catch (e) { alert(e.message) } finally { setBusyId(null) }
  }

  const filtered = search || prediction || status
  return (
    <div>
      <PageHeader title="Analysis History" subtitle="Every analysis stored in MongoDB. Search, filter, reopen or delete." />
      <div className="panel mb-5 grid gap-3 p-4 sm:grid-cols-[1fr_auto_auto]">
        <div className="relative"><Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-500" /><input className="input !pl-10" placeholder="Search headlines…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search headlines" /></div>
        <select className="input" value={prediction} onChange={(e) => setPrediction(e.target.value)} aria-label="Filter by prediction"><option value="">All predictions</option><option value="REAL">REAL</option><option value="FAKE">FAKE</option></select>
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by verification status">
          <option value="">All verification</option><option>Pending</option><option>Supporting evidence found</option><option>Contradicting evidence found</option><option>Mixed evidence</option><option>Insufficient evidence</option>
        </select>
      </div>

      {loading ? <Spinner /> : error ? <ErrorState error={error} onRetry={reload} /> : data.length === 0 ? (
        <EmptyState title={filtered ? 'No matches' : 'No history yet'} hint={filtered ? 'Try different filters.' : 'Analyses you run will appear here.'} action={!filtered && <Link to="/app/analyze" className="btn-primary mt-3">Start analysing</Link>} />
      ) : (
        <div className="space-y-2">
          {data.map((r) => (
            <div key={r.id} className="panel panel-hover flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="min-w-0 flex-1 basis-64">
                <p className="truncate font-medium text-slate-900">{r.headline}</p>
                <p className="mt-0.5 text-xs text-slate-500">{fmtDate(r.created_at)} · {r.model_name}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={predictionTone(r.prediction)}>{r.prediction}</Badge>
                <span className="font-mono text-xs text-slate-600">{pct(r.confidence, 1)}</span>
                <Badge tone={r.verification_status === 'Pending' ? 'mute' : evidenceTone(r.verification_status)}>{r.verification_status}</Badge>
                <Link to={`/app/history/${r.id}`} className="btn-ghost !px-3 !py-1.5"><Eye className="h-4 w-4" /> View</Link>
                <button className="btn-danger !px-3 !py-1.5" onClick={() => remove(r.id)} disabled={busyId === r.id} aria-label="Delete analysis"><Trash2 className="h-4 w-4" /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const { id } = useParams()
  return id ? <Detail id={id} /> : <List />
}
