import { Link } from 'react-router-dom'
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Activity, CheckCircle2, Clock, FileSearch, ScanSearch, ShieldAlert } from 'lucide-react'
import { motion } from 'framer-motion'
import { Badge, EmptyState, ErrorState, PageHeader, Section, Spinner, fmtDate, pct, predictionTone } from '../components/ui'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'

const COLORS = { REAL: '#34d399', FAKE: '#fb7185' }

function Stat({ icon: Icon, label, value, tone, i }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="panel panel-hover p-5">
      <div className="mb-3 flex items-center justify-between"><span className="label">{label}</span><Icon className={`h-4 w-4 ${tone}`} /></div>
      <p className="text-3xl font-bold tracking-tight text-slate-900">{value}</p>
    </motion.div>
  )
}

const tooltipStyle = { background: '#ffffff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, fontSize: 12 }

export default function Dashboard() {
  const { data, error, loading, reload } = useFetch(api.dashboard, [])
  if (loading) return <Spinner />
  if (error) return <ErrorState error={error} onRetry={reload} />
  const { totals, distribution, activity, recent, model, database } = data

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Live statistics from your stored analyses and the trained model.">
        <Link to="/app/analyze" className="btn-primary"><ScanSearch className="h-4 w-4" /> Quick analysis</Link>
      </PageHeader>

      {!database.available && (
        <div className="panel mb-6 border-amber-400/20 p-4 text-sm text-amber-800">
          MongoDB is not connected, so statistics and history are disabled. Analysis still works. <span className="text-amber-700/80">{database.error}</span>
        </div>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat i={0} icon={FileSearch} label="Articles analysed" value={totals.total} tone="text-accent" />
        <Stat i={1} icon={ShieldAlert} label="Fake predictions" value={totals.fake} tone="text-rose-400" />
        <Stat i={2} icon={CheckCircle2} label="Real predictions" value={totals.real} tone="text-emerald-400" />
        <Stat i={3} icon={Clock} label="Pending verification" value={totals.pending} tone="text-amber-400" />
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <Section title="Fake vs real (classifier)" icon={Activity}>
            {totals.total === 0 ? <p className="py-10 text-center text-sm text-slate-500">No analyses yet.</p> : (
              <div className="h-56">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={distribution} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3} stroke="none">
                      {distribution.map((d) => <Cell key={d.name} fill={COLORS[d.name]} />)}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="mt-2 flex justify-center gap-5 text-xs text-slate-600">
              {distribution.map((d) => <span key={d.name}><span className="mr-1.5 inline-block h-2 w-2 rounded-full" style={{ background: COLORS[d.name] }} />{d.name} {d.value}</span>)}
            </div>
          </Section>
        </div>
        <div className="lg:col-span-3">
          <Section title="Daily analysis activity (14 days)" icon={Activity}>
            <div className="h-60">
              <ResponsiveContainer>
                <AreaChart data={activity} margin={{ left: -20, right: 8, top: 8 }}>
                  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#0891b2" stopOpacity={0.4} /><stop offset="100%" stopColor="#0891b2" stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid stroke="rgba(15,23,42,0.08)" vertical={false} />
                  <XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis allowDecimals={false} stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="count" name="Analyses" stroke="#0891b2" strokeWidth={2} fill="url(#g)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Section>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Section title="Recent analyses" icon={Clock}>
            {recent.length === 0 ? <EmptyState title="Nothing analysed yet" hint="Run your first analysis to see it here." action={<Link to="/app/analyze" className="btn-primary mt-3">Start analysing</Link>} /> : (
              <ul className="divide-y divide-slate-100">
                {recent.map((r) => (
                  <li key={r.id}>
                    <Link to={`/app/history/${r.id}`} className="flex items-center justify-between gap-3 py-3 transition hover:text-accent">
                      <div className="min-w-0"><p className="truncate text-sm font-medium text-slate-900">{r.headline}</p><p className="text-xs text-slate-500">{fmtDate(r.created_at)}</p></div>
                      <div className="flex shrink-0 items-center gap-2"><span className="font-mono text-xs text-slate-600">{pct(r.confidence, 0)}</span><Badge tone={predictionTone(r.prediction)}>{r.prediction}</Badge></div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </div>
        <div className="lg:col-span-2">
          <Section title="Model performance" icon={Activity} note="Measured on the held-out 20% test split during training.">
            {model.trained ? (
              <>
                <p className="mb-4 text-sm text-slate-700">Best model: <span className="font-semibold text-slate-900">{model.best_model}</span></p>
                {[['Accuracy', model.accuracy], ['Precision', model.precision], ['Recall', model.recall], ['F1-score', model.f1]].map(([k, v]) => (
                  <div key={k} className="mb-3"><div className="mb-1 flex justify-between text-xs text-slate-600"><span>{k}</span><span className="font-mono text-slate-800">{pct(v, 2)}</span></div><div className="h-1.5 rounded-full bg-slate-100"><div className="h-full rounded-full bg-accent" style={{ width: `${v * 100}%` }} /></div></div>
                ))}
              </>
            ) : <p className="text-sm text-slate-600">No trained model yet. Add the dataset and run <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs">python ml/train.py</code>.</p>}
          </Section>
        </div>
      </div>
    </div>
  )
}
