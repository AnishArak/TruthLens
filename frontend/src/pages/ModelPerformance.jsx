import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Trophy } from 'lucide-react'
import { Badge, EmptyState, ErrorState, PageHeader, Section, Spinner, fmtDate, pct } from '../components/ui'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'

function ConfusionMatrix({ m }) {
  const max = Math.max(...m.confusion_matrix.flat(), 1)
  return (
    <div className="inline-block">
      <p className="label mb-2 text-center">Predicted</p>
      <div className="flex items-center gap-2">
        <span className="label -rotate-90 whitespace-nowrap">Actual</span>
        <table className="border-separate border-spacing-1.5 text-center text-sm">
          <thead><tr><th />{m.labels.map((l) => <th key={l} className="label px-2">{l}</th>)}</tr></thead>
          <tbody>
            {m.confusion_matrix.map((row, i) => (
              <tr key={i}>
                <th className="label pr-2 text-right">{m.labels[i]}</th>
                {row.map((v, j) => (
                  <td key={j} className="h-20 w-28 rounded-xl font-mono text-lg font-semibold text-slate-900" style={{ background: `rgba(${i === j ? '52,211,153' : '251,113,133'},${0.12 + 0.55 * (v / max)})` }}>{v.toLocaleString()}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function ModelPerformance() {
  const { data, error, loading, reload } = useFetch(api.modelMetrics, [])
  const [selected, setSelected] = useState(null)
  if (loading) return <Spinner />
  if (error) return <ErrorState error={error} onRetry={reload} />
  if (!data.trained) return <div><PageHeader title="Model Performance" /><EmptyState title="No trained model yet" hint={data.message} /></div>

  const active = data.models.find((m) => m.name === (selected || data.best_model))
  const chart = data.models.map((m) => ({ name: m.name.replace('Multinomial ', ''), Accuracy: +(m.accuracy * 100).toFixed(2), Precision: +(m.precision * 100).toFixed(2), Recall: +(m.recall * 100).toFixed(2), 'F1-score': +(m.f1 * 100).toFixed(2) }))
  const report = active.classification_report

  return (
    <div>
      <PageHeader title="Model Performance" subtitle={`Real results from the held-out test set (${data.n_test.toLocaleString()} articles). Trained ${fmtDate(data.trained_at)} · seed ${data.seed}.`} />
      {data.sampled_run && <div className="panel mb-5 border-amber-400/20 p-4 text-sm text-amber-800">These metrics come from a sampled quick run (<code>--sample</code>). Re-train on the full dataset for final results.</div>}

      <Section title="Comparison" icon={Trophy} note="Precision, recall and F1 are for the FAKE class. The best model is selected by highest F1-score on the test set.">
        <div className="h-64">
          <ResponsiveContainer>
            <BarChart data={chart} margin={{ left: -10 }}>
              <CartesianGrid stroke="rgba(15,23,42,0.08)" vertical={false} />
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} unit="%" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Accuracy" fill="#0891b2" radius={[4, 4, 0, 0]} /><Bar dataKey="Precision" fill="#34d399" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Recall" fill="#a78bfa" radius={[4, 4, 0, 0]} /><Bar dataKey="F1-score" fill="#fbbf24" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr className="label border-b border-slate-100"><th className="py-2">Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>Train time</th></tr></thead>
            <tbody>
              {data.models.map((m) => (
                <tr key={m.name} className="cursor-pointer border-b border-slate-100 transition hover:bg-slate-50" onClick={() => setSelected(m.name)}>
                  <td className="py-3 font-medium text-slate-900">{m.name} {m.name === data.best_model && <Badge tone="info" className="ml-2">Best</Badge>}</td>
                  <td className="font-mono">{pct(m.accuracy, 2)}</td><td className="font-mono">{pct(m.precision, 2)}</td><td className="font-mono">{pct(m.recall, 2)}</td><td className="font-mono">{pct(m.f1, 2)}</td><td className="font-mono text-slate-500">{m.train_seconds}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Section title={`Confusion matrix — ${active.name}`}>
          <div className="flex justify-center overflow-x-auto"><ConfusionMatrix m={active} /></div>
          <p className="mt-3 text-center text-xs text-slate-500">Select a model in the table above to switch.</p>
        </Section>
        <Section title={`Classification report — ${active.name}`}>
          <table className="w-full text-sm">
            <thead><tr className="label border-b border-slate-100 text-left"><th className="py-2">Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead>
            <tbody>
              {['REAL', 'FAKE', 'macro avg', 'weighted avg'].map((k) => (
                <tr key={k} className="border-b border-slate-100"><td className="py-2.5 font-medium text-slate-900">{k}</td><td className="font-mono">{report[k].precision.toFixed(4)}</td><td className="font-mono">{report[k].recall.toFixed(4)}</td><td className="font-mono">{report[k]['f1-score'].toFixed(4)}</td><td className="font-mono text-slate-500">{report[k].support}</td></tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>
    </div>
  )
}
