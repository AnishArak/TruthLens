import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, BarChart3, Brain, FileSearch, Globe2, Lightbulb, Search, ShieldCheck, Sparkles, Tags } from 'lucide-react'
import { Logo } from '../components/ui'

const FEATURES = [
  { icon: Brain, title: 'ML classification', text: 'Logistic Regression, Naive Bayes and Linear SVM trained on real data; the best model by F1 is used.' },
  { icon: Lightbulb, title: 'Explainable AI', text: 'LIME highlights the words that pushed the model towards REAL or FAKE — with honest limitations.' },
  { icon: Search, title: 'Evidence verification', text: 'Claims are extracted and compared with retrieved sources. Nothing is invented without a search provider.' },
  { icon: Globe2, title: 'Source credibility', text: 'Domain, HTTPS and publisher identity checked against an editable source database.' },
  { icon: Tags, title: 'Clickbait & sentiment', text: 'Transparent rule-based sensationalism indicators plus VADER sentiment.' },
  { icon: BarChart3, title: 'Analytics dashboard', text: 'History and statistics stored in MongoDB, with real model metrics from your own training run.' },
]
const STEPS = [
  ['Submit', 'Paste an article, enter a headline or provide a URL.'],
  ['Analyse', 'NLP features, classifier prediction and LIME explanation are computed.'],
  ['Verify', 'Key claims are searched against live sources when a provider is configured.'],
  ['Decide', 'Review three separate outcomes and make your own judgement.'],
]
const STACK = ['React', 'Vite', 'Tailwind CSS', 'Framer Motion', 'Recharts', 'Flask', 'scikit-learn', 'NLTK', 'LIME', 'VADER', 'Sentence-Transformers', 'MongoDB', 'BeautifulSoup']

const rise = (d = 0) => ({ initial: { opacity: 0, y: 18 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true }, transition: { duration: 0.5, delay: d } })

export default function Landing() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Logo className="text-xl" />
        <nav className="flex items-center gap-2">
          <Link to="/app/about" className="btn-ghost hidden sm:inline-flex">About</Link>
          <Link to="/app" className="btn-primary">Open app</Link>
        </nav>
      </header>

      <section className="mx-auto max-w-4xl px-5 pb-16 pt-16 text-center sm:pt-24">
        <motion.div {...rise()} className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-3.5 py-1 text-xs font-medium text-accent"><Sparkles className="h-3.5 w-3.5" /> NLP · Machine Learning · Explainable AI</motion.div>
        <motion.h1 {...rise(0.05)} className="text-4xl font-extrabold leading-[1.05] tracking-tight text-slate-900 sm:text-6xl">Don’t Just Read the News.<br /><span className="bg-gradient-to-r from-accent to-accent-green bg-clip-text text-transparent">Verify It.</span></motion.h1>
        <motion.p {...rise(0.1)} className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-slate-600 sm:text-lg">TruthLens analyses articles, headlines and URLs with NLP, explains what influenced its prediction and checks claims against real evidence — keeping the model’s opinion, the evidence and the source clearly separate.</motion.p>
        <motion.div {...rise(0.15)} className="mt-9 flex flex-wrap justify-center gap-3"><Link to="/app/analyze" className="btn-primary !px-6 !py-3">Start Analysing <ArrowRight className="h-4 w-4" /></Link><Link to="/app/models" className="btn-ghost !px-6 !py-3">See model results</Link></motion.div>

        {/* Static preview of the analyzer input; clicking goes to the real page */}
        <motion.div {...rise(0.2)} className="mx-auto mt-14 max-w-2xl text-left">
          <Link to="/app/analyze" className="panel panel-hover block p-4 shadow-glow">
            <div className="mb-3 flex gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-rose-400/60" /><span className="h-2.5 w-2.5 rounded-full bg-amber-400/60" /><span className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" /></div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">Paste a news article, headline or URL to analyse…</div>
            <div className="mt-3 flex items-center justify-between text-xs text-slate-500"><span className="flex items-center gap-1.5"><FileSearch className="h-3.5 w-3.5" /> Article · Headline · URL</span><span className="rounded-lg bg-accent px-3 py-1.5 font-semibold text-white">Analyse</span></div>
          </Link>
        </motion.div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="mb-2 text-center text-2xl font-bold text-slate-900 sm:text-3xl">Built for critical reading</h2>
        <p className="mx-auto mb-10 max-w-xl text-center text-sm text-slate-600">Every result comes from real model output. If something can’t be computed, TruthLens says so.</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div key={f.title} {...rise(i * 0.05)} className="panel panel-hover p-6">
              <div className="mb-4 inline-flex rounded-xl bg-accent/10 p-2.5"><f.icon className="h-5 w-5 text-accent" /></div>
              <h3 className="font-semibold text-slate-900">{f.title}</h3><p className="mt-1.5 text-sm leading-relaxed text-slate-600">{f.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="mb-10 text-center text-2xl font-bold text-slate-900 sm:text-3xl">How it works</h2>
        <div className="grid gap-4 md:grid-cols-4">
          {STEPS.map(([t, d], i) => (
            <motion.div key={t} {...rise(i * 0.07)} className="relative rounded-2xl border border-slate-200 p-6">
              <span className="font-mono text-xs text-accent">0{i + 1}</span><h3 className="mt-2 font-semibold text-slate-900">{t}</h3><p className="mt-1.5 text-sm text-slate-600">{d}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 text-center">
        <h2 className="mb-8 text-2xl font-bold text-slate-900 sm:text-3xl">Technology</h2>
        <div className="flex flex-wrap justify-center gap-2.5">{STACK.map((s) => <span key={s} className="rounded-full border border-slate-200 bg-slate-50 px-4 py-1.5 text-sm text-slate-700 transition hover:border-accent/40 hover:text-slate-900">{s}</span>)}</div>
      </section>

      <section className="mx-auto max-w-3xl px-5 pb-20">
        <div className="panel p-8 text-center"><ShieldCheck className="mx-auto mb-3 h-7 w-7 text-accent-green" /><p className="text-sm leading-relaxed text-slate-600">A text classifier cannot establish whether a claim is true. TruthLens reports its prediction, the evidence it could retrieve and the source information as three separate results — you make the call.</p></div>
      </section>

      <footer className="border-t border-slate-100 py-8 text-center text-xs text-slate-500">
        <Logo className="mb-3 text-sm" /><p>TruthLens — an academic NLP project. Predictions are not statements of fact.</p>
      </footer>
    </div>
  )
}
