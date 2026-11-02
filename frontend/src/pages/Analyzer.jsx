import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { FileText, Link2, Loader2, ScanSearch, Type, AlertTriangle } from 'lucide-react'
import AnalysisResult from '../components/AnalysisResult'
import { Badge, PageHeader } from '../components/ui'
import { api } from '../services/api'

const MODES = [
  { id: 'article', label: 'Paste article', icon: FileText, min: 100, max: 50000, placeholder: 'Paste the full news article here (at least 100 characters)…' },
  { id: 'headline', label: 'Headline', icon: Type, min: 10, max: 300, placeholder: 'Enter a news headline (at least 10 characters)…' },
  { id: 'url', label: 'Article URL', icon: Link2, placeholder: 'https://example.com/news/article' },
]

function validate(mode, value) {
  const v = value.trim()
  if (!v) return 'Please enter something to analyse.'
  if (mode.id === 'url') {
    try {
      const u = new URL(v.includes('://') ? v : `https://${v}`)
      if (!['http:', 'https:'].includes(u.protocol)) return 'Only http and https URLs are supported.'
      if (!u.hostname.includes('.')) return 'That does not look like a valid URL.'
    } catch {
      return 'That does not look like a valid URL.'
    }
    return null
  }
  if (v.length < mode.min) return `Too short — enter at least ${mode.min} characters (currently ${v.length}).`
  if (v.length > mode.max) return `Too long — maximum ${mode.max} characters.`
  return null
}

export default function Analyzer() {
  const [modeId, setModeId] = useState('article')
  const [value, setValue] = useState('')
  const [touched, setTouched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const mode = MODES.find((m) => m.id === modeId)
  const problem = touched ? validate(mode, value) : null

  async function submit(e) {
    e.preventDefault()
    setTouched(true)
    if (validate(mode, value)) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = modeId === 'url' ? await api.analyzeUrl(value.trim()) : await api.analyze({ mode: modeId, text: value.trim() })
      setResult(res.data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader title="News Analyzer" subtitle="Classify an article, then inspect the explanation, claims, evidence and source — each reported separately." />

      <form onSubmit={submit} className="panel mb-6 p-5 sm:p-6" noValidate>
        <div className="mb-4 flex flex-wrap gap-2" role="tablist">
          {MODES.map((m) => (
            <button key={m.id} type="button" role="tab" aria-selected={m.id === modeId}
              onClick={() => { setModeId(m.id); setValue(''); setTouched(false); setError(null) }}
              className={`btn !py-2 ${m.id === modeId ? 'bg-accent/10 text-accent ring-1 ring-accent/40' : 'text-slate-600 hover:bg-slate-100'}`}>
              <m.icon className="h-4 w-4" /> {m.label}
            </button>
          ))}
        </div>

        {modeId === 'url' ? (
          <input className="input" value={value} onChange={(e) => setValue(e.target.value)} placeholder={mode.placeholder} aria-label="Article URL" />
        ) : (
          <textarea className="input min-h-[200px] resize-y leading-relaxed" rows={modeId === 'headline' ? 3 : 10} value={value}
            onChange={(e) => setValue(e.target.value)} placeholder={mode.placeholder} aria-label={mode.label} />
        )}

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs">
            {problem ? <span className="text-rose-700">{problem}</span>
              : modeId === 'url' ? <span className="text-slate-500">Public http/https pages only. Local and private addresses are blocked.</span>
              : <span className={value.length > mode.max ? 'text-rose-700' : 'text-slate-500'}>{value.length.toLocaleString()} / {mode.max.toLocaleString()} characters</span>}
          </div>
          <button className="btn-primary" disabled={loading}>
            {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Analysing…</> : <><ScanSearch className="h-4 w-4" /> Analyse</>}
          </button>
        </div>
      </form>

      <AnimatePresence mode="wait">
        {loading && (
          <motion.div key="load" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="panel p-10 text-center">
            <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-accent" />
            <p className="text-sm text-slate-700">Running classifier, explanation, NLP and evidence checks…</p>
            <p className="mt-1 text-xs text-slate-500">The first run can take longer while models load.</p>
          </motion.div>
        )}
        {error && !loading && (
          <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="panel border-rose-400/20 p-6" role="alert">
            <p className="flex items-center gap-2 font-semibold text-rose-700"><AlertTriangle className="h-4 w-4" /> Analysis failed</p>
            <p className="mt-2 text-sm text-slate-700">{error.message}</p>
            {['EXTRACTION_FAILED', 'ROBOTS_DISALLOWED', 'FETCH_FAILED', 'FETCH_HTTP_ERROR', 'FETCH_TIMEOUT'].includes(error.code) && (
              <button className="btn-ghost mt-4" type="button" onClick={() => { setModeId('article'); setValue(''); setError(null) }}>Paste the article text instead</button>
            )}
          </motion.div>
        )}
        {result && !loading && (
          <motion.div key="res" className="space-y-4">
            {!result.persistence?.saved && (
              <div className="panel border-amber-400/20 p-4 text-sm text-amber-800"><Badge tone="warn">Not saved</Badge> <span className="ml-2">{result.persistence?.message}</span></div>
            )}
            <AnalysisResult result={result} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
