import { motion } from 'framer-motion'
import { AlertCircle, ExternalLink, Gauge, Globe2, Lightbulb, Link2, ShieldCheck, Sparkles, Tags, Brain, Search } from 'lucide-react'
import { Badge, Section, evidenceTone, fmtDate, pct, predictionTone } from './ui'

const fade = { initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.35 } }

/** Wrap influential words inside the excerpt with coloured marks. */
function HighlightedText({ text, features }) {
  if (!features?.length) return <p className="text-sm leading-relaxed text-slate-700">{text}</p>
  const map = new Map(features.map((f) => [f.word.toLowerCase(), f]))
  const parts = text.split(/([A-Za-z']+)/)
  return (
    <p className="text-sm leading-relaxed text-slate-700">
      {parts.map((p, i) => {
        const f = map.get(p.toLowerCase())
        if (!f) return p
        const cls = f.weight > 0 ? 'bg-rose-400/20 text-rose-800' : 'bg-emerald-400/20 text-emerald-800'
        return (
          <mark key={i} className={`rounded px-0.5 ${cls}`} title={`${f.pushes_towards} • weight ${f.weight.toFixed(3)}`}>
            {p}
          </mark>
        )
      })}
    </p>
  )
}

function Outcome({ icon: Icon, title, badge, children }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="label mb-2 flex items-center gap-2"><Icon className="h-3.5 w-3.5 text-accent" /> {title}</p>
      <div className="mb-2">{badge}</div>
      <p className="text-xs leading-relaxed text-slate-600">{children}</p>
    </div>
  )
}

export default function AnalysisResult({ result }) {
  const { classification: c, explanation: x, nlp, evidence: ev, source: src } = result
  const sent = nlp.sentiment
  const maxW = Math.max(0.001, ...(x?.features || []).map((f) => Math.abs(f.weight)))

  return (
    <motion.div {...fade} className="space-y-5">
      {/* ---- Final result: three separate outcomes, deliberately not merged into one score ---- */}
      <Section title="Final result" icon={ShieldCheck} note="These three outcomes are independent and are intentionally not combined into a single truth score.">
        <div className="grid gap-3 md:grid-cols-3">
          <Outcome icon={Brain} title="ML classification" badge={<Badge tone={predictionTone(c.label)}>{c.label} · {pct(c.confidence, 1)} model confidence</Badge>}>
            Style-pattern prediction by {c.model_name}. Not a fact check.
          </Outcome>
          <Outcome icon={Search} title="Evidence verification" badge={<Badge tone={evidenceTone(ev.label)}>{ev.label}</Badge>}>
            {ev.status === 'ok' ? `${ev.evidence.length} related source(s) retrieved via ${ev.provider}.` : ev.reason}
          </Outcome>
          <Outcome icon={Globe2} title="Source assessment"
            badge={<Badge tone={src.available ? (src.reputation?.listed ? 'info' : 'mute') : 'mute'}>{src.available ? (src.reputation?.name || 'Unlisted source') : 'Not available'}</Badge>}>
            {src.available ? src.assessment : src.reason}
          </Outcome>
        </div>
      </Section>

      {/* ---- Prediction ---- */}
      <Section title="Prediction" icon={Gauge} note={c.disclaimer}>
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <p className={`text-4xl font-extrabold tracking-tight ${c.label === 'FAKE' ? 'text-rose-700' : 'text-emerald-700'}`}>{c.label}</p>
            <p className="mt-1 text-xs text-slate-600">Model: {c.model_name}</p>
          </div>
          <div className="min-w-[220px] flex-1">
            <div className="mb-1 flex justify-between text-xs text-slate-600"><span>Model confidence</span><span className="font-mono text-slate-800">{pct(c.confidence)}</span></div>
            <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
              <motion.div className={`h-full rounded-full ${c.label === 'FAKE' ? 'bg-rose-400' : 'bg-emerald-400'}`} initial={{ width: 0 }} animate={{ width: `${c.confidence * 100}%` }} transition={{ duration: 0.8 }} />
            </div>
            <div className="mt-2 flex justify-between text-[11px] text-slate-500">
              <span>REAL {pct(c.probabilities.REAL)}</span><span>FAKE {pct(c.probabilities.FAKE)}</span>
            </div>
          </div>
        </div>
      </Section>

      {/* ---- NLP ---- */}
      <Section title="NLP analysis" icon={Tags} note={nlp.clickbait.note}>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <p className="label mb-2">Keywords</p>
            <div className="flex flex-wrap gap-1.5">
              {nlp.keywords.map((k) => <Badge key={k.keyword} tone="info">{k.keyword} <span className="opacity-60">×{k.count}</span></Badge>)}
            </div>
            <p className="label mb-2 mt-5">Important phrases</p>
            <div className="flex flex-wrap gap-1.5">
              {nlp.phrases.length ? nlp.phrases.map((p) => <Badge key={p.phrase}>{p.phrase}</Badge>) : <span className="text-xs text-slate-500">None found</span>}
            </div>
          </div>
          <div className="space-y-5">
            <div>
              <p className="label mb-2">Sentiment (VADER)</p>
              {sent.available ? (
                <>
                  <div className="flex items-center gap-3">
                    <Badge tone={sent.label === 'Positive' ? 'real' : sent.label === 'Negative' ? 'fake' : 'mute'}>{sent.label}</Badge>
                    <span className="font-mono text-xs text-slate-600">compound {sent.compound}</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">pos {sent.positive} · neu {sent.neutral} · neg {sent.negative}</p>
                  {sent.emotive_words?.length > 0 && (
                    <p className="mt-2 text-xs text-slate-600">Emotive words: {sent.emotive_words.map((w) => w.word).join(', ')}</p>
                  )}
                </>
              ) : <p className="text-xs text-amber-700">{sent.reason}</p>}
            </div>
            <div>
              <p className="label mb-2">Clickbait / sensationalism (rule-based)</p>
              <div className="mb-1 flex items-center justify-between text-xs"><Badge tone={nlp.clickbait.level === 'High' ? 'fake' : nlp.clickbait.level === 'Moderate' ? 'warn' : 'real'}>{nlp.clickbait.level}</Badge><span className="font-mono text-slate-700">{nlp.clickbait.score}/100</span></div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-amber-400" style={{ width: `${nlp.clickbait.score}%` }} /></div>
              <ul className="mt-2 space-y-1 text-xs text-slate-600">
                {nlp.clickbait.indicators.length ? nlp.clickbait.indicators.map((i, k) => <li key={k}>• “{i.match}” <span className="text-slate-400">({i.location}, +{i.points})</span></li>) : <li>No sensational indicators detected.</li>}
              </ul>
              <p className="mt-2 text-[11px] text-slate-400">{nlp.clickbait.method}</p>
            </div>
          </div>
        </div>
      </Section>

      {/* ---- XAI ---- */}
      <Section title="Explainable AI" icon={Lightbulb} note={x?.available ? x.limitations : undefined}>
        {x?.available ? (
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <p className="label mb-2">Influential words in the text</p>
              <HighlightedText text={result.excerpt} features={x.features} />
              <p className="mt-3 flex gap-4 text-[11px] text-slate-500"><span><span className="mr-1 inline-block h-2 w-2 rounded bg-rose-400/60" />pushes towards FAKE</span><span><span className="mr-1 inline-block h-2 w-2 rounded bg-emerald-400/60" />pushes towards REAL</span></p>
              {x.truncated && <p className="mt-2 text-[11px] text-amber-700/90">Only the first 400 content words were explained.</p>}
            </div>
            <div>
              <p className="label mb-2">Feature contributions ({x.method})</p>
              <ul className="space-y-1.5">
                {x.features.map((f) => (
                  <li key={f.word} className="flex items-center gap-2 text-xs">
                    <span className="w-24 shrink-0 truncate font-mono text-slate-700">{f.word}</span>
                    <div className="relative h-2 flex-1 rounded bg-slate-100">
                      <div className={`absolute top-0 h-full rounded ${f.weight > 0 ? 'left-1/2 bg-rose-400' : 'right-1/2 bg-emerald-400'}`} style={{ width: `${(Math.abs(f.weight) / maxW) * 50}%` }} />
                    </div>
                    <span className="w-14 text-right font-mono text-slate-500">{f.weight.toFixed(3)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="flex items-start gap-2 text-sm text-amber-700"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> Explanation unavailable: {x?.reason}</p>
        )}
      </Section>

      {/* ---- Evidence ---- */}
      <Section title="Evidence verification" icon={Search} note={ev.method_notes?.join(' ')}>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Badge tone={evidenceTone(ev.label)}>{ev.label}</Badge>
          {ev.provider && <span className="text-xs text-slate-500">via {ev.provider}{ev.similarity_method ? ` · ${ev.similarity_method}` : ''}</span>}
        </div>
        {ev.status !== 'ok' && (
          <p className="mb-4 flex items-start gap-2 rounded-xl border border-amber-400/20 bg-amber-400/5 p-3 text-sm text-amber-800"><AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />{ev.reason}</p>
        )}
        <p className="label mb-2">Extracted claims</p>
        {ev.claims.length ? (
          <ol className="mb-5 list-decimal space-y-1.5 pl-5 text-sm text-slate-700">{ev.claims.map((cl, i) => <li key={i}>{cl.claim}<span className="ml-2 font-mono text-[11px] text-slate-400">q: {cl.query}</span></li>)}</ol>
        ) : <p className="mb-5 text-xs text-slate-500">No check-worthy claims extracted.</p>}
        {ev.evidence.length > 0 && (
          <div className="space-y-2">
            <p className="label">Retrieved evidence</p>
            {ev.evidence.map((e, i) => (
              <a key={i} href={e.url} target="_blank" rel="noopener noreferrer" className="panel panel-hover block p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="text-sm font-medium text-slate-900">{e.title} <ExternalLink className="ml-1 inline h-3 w-3 text-slate-500" /></p>
                  <Badge tone={e.stance === 'supports' ? 'real' : 'fake'}>{e.stance === 'supports' ? 'Supports (heuristic)' : 'Contradicts (heuristic)'}</Badge>
                </div>
                {e.snippet && <p className="mt-1 text-xs text-slate-600">{e.snippet}</p>}
                <p className="mt-2 text-[11px] text-slate-500">{e.source || 'Unknown source'} · {e.published_at ? fmtDate(e.published_at) : 'date n/a'} · relevance {pct(e.relevance, 0)}</p>
              </a>
            ))}
          </div>
        )}
      </Section>

      {/* ---- Source ---- */}
      <Section title="Source assessment" icon={Link2}>
        {src.available ? (
          <dl className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2">
            <div><dt className="label">Domain</dt><dd className="font-mono text-slate-800">{src.domain}</dd></div>
            <div><dt className="label">HTTPS</dt><dd>{src.https === null ? 'Unknown' : src.https ? 'Yes' : 'No'}</dd></div>
            <div><dt className="label">Publisher</dt><dd>{src.publisher_name || 'Unknown'} <span className="text-xs text-slate-500">{src.publisher_name_source && `(${src.publisher_name_source})`}</span></dd></div>
            <div><dt className="label">Category</dt><dd>{src.reputation.category.replace('_', ' ')}</dd></div>
            <div className="sm:col-span-2"><dt className="label">Assessment</dt><dd className="text-slate-700">{src.assessment}</dd></div>
            {result.article?.author && <div><dt className="label">Author</dt><dd>{result.article.author}</dd></div>}
            {result.article?.published_at && <div><dt className="label">Published</dt><dd>{result.article.published_at}</dd></div>}
          </dl>
        ) : <p className="text-sm text-slate-600">{src.reason}</p>}
      </Section>

      <p className="text-center text-xs text-slate-400"><Sparkles className="mr-1 inline h-3 w-3" />Analysed {fmtDate(result.created_at)}</p>
    </motion.div>
  )
}
