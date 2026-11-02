import { Brain, Database, FlaskConical, Layers, Lightbulb, Rocket, ShieldAlert } from 'lucide-react'
import { PageHeader, Section } from '../components/ui'

const Li = ({ children }) => <li className="flex gap-2"><span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" /><span>{children}</span></li>
const List = ({ children }) => <ul className="space-y-2 text-sm leading-relaxed text-slate-700">{children}</ul>

export default function About() {
  return (
    <div className="space-y-5">
      <PageHeader title="About TruthLens" subtitle="An academic NLP project combining a text classifier, explainable AI and evidence-based verification — kept deliberately separate." />

      <Section title="NLP concepts used" icon={Brain}>
        <List>
          <Li><b>Text normalisation &amp; tokenization</b> — lower-casing, removal of URLs/HTML/agency datelines, regex word tokenization.</Li>
          <Li><b>Stopword removal</b> — NLTK English list (with a built-in fallback). Stemming and lemmatization are optional and are <i>not</i> applied in the default pipeline.</Li>
          <Li><b>TF-IDF</b> — weights terms by how distinctive they are; unigrams and bigrams, sublinear term frequency.</Li>
          <Li><b>Sentiment analysis</b> — VADER, a lexicon- and rule-based scorer.</Li>
          <Li><b>Semantic similarity</b> — cosine similarity between a claim and retrieved text, using Sentence-Transformers when enabled, otherwise a labelled TF-IDF fallback.</Li>
          <Li><b>Claim extraction</b> — heuristic ranking of sentences by figures, named entities and reporting verbs.</Li>
        </List>
      </Section>

      <Section title="Machine-learning algorithms" icon={FlaskConical}>
        <List>
          <Li><b>Logistic Regression</b> — linear model producing calibrated class probabilities.</Li>
          <Li><b>Multinomial Naive Bayes</b> — probabilistic model that assumes conditionally independent term counts.</Li>
          <Li><b>Linear SVM</b> — maximum-margin linear classifier (wrapped in probability calibration so it can report confidence and work with LIME).</Li>
          <Li>The best model is chosen by <b>F1-score</b> on a held-out test set and saved with Joblib.</Li>
        </List>
      </Section>

      <Section title="Dataset &amp; training methodology" icon={Database}>
        <List>
          <Li>Kaggle <i>Fake and Real News Dataset</i> (Fake.csv and True.csv). Label 1 = FAKE, 0 = REAL.</Li>
          <Li>Missing values handled, duplicate and label-conflicting articles removed, title and text combined.</Li>
          <Li>Stratified 80/20 split with a fixed random seed. Each pipeline fits TF-IDF <b>only on training data</b> to prevent leakage.</Li>
          <Li>News-agency datelines (e.g. “WASHINGTON (Reuters) -”) are stripped because they almost only occur in the REAL class and would let a model “cheat”.</Li>
          <Li>All numbers on the Model Performance page are computed from real predictions on the test split.</Li>
        </List>
      </Section>

      <Section title="Architecture" icon={Layers}>
        <List>
          <Li><b>Frontend</b>: React + Vite + Tailwind, talking to a REST API.</Li>
          <Li><b>Backend</b>: Flask services for classification, LIME, NLP, URL extraction (SSRF-protected), source lookup and evidence retrieval.</Li>
          <Li><b>Storage</b>: MongoDB for history (privacy-conscious excerpts, not full articles). Analysis still works without it.</Li>
          <Li><b>Three independent outcomes</b>: ML classification, evidence verification and source assessment are never merged into one “truth score”.</Li>
        </List>
      </Section>

      <Section title="Limitations" icon={ShieldAlert}>
        <List>
          <Li>The classifier learns <b>writing-style patterns of its training data</b> (2016–2017 US news). It does not know whether a claim is true and may generalise poorly to other topics, regions or eras.</Li>
          <Li>High confidence is not factual certainty. Real news can be sensational; fake news can be calm and well written.</Li>
          <Li>LIME explanations are local, word-level approximations and reflect correlations, not causes.</Li>
          <Li>Evidence stance (supports/contradicts) is a simple negation-cue heuristic, not natural-language inference. Retrieval quality depends on the configured search provider, and is unavailable without one.</Li>
          <Li>Clickbait detection is a transparent rule-based baseline, not a trained model.</Li>
          <Li>The source database is a small, editable starter list. An unlisted domain is unrated, not unreliable.</Li>
        </List>
      </Section>

      <Section title="Future enhancements" icon={Rocket}>
        <List>
          <Li>Transformer classifier (e.g. fine-tuned BERT/RoBERTa) and cross-domain evaluation.</Li>
          <Li>Natural-language-inference model for evidence stance instead of heuristics.</Li>
          <Li>Integration with fact-check claim databases; multilingual support.</Li>
          <Li>User accounts, saved collections and browser extension.</Li>
        </List>
      </Section>
      <p className="flex items-center justify-center gap-2 pt-2 text-xs text-slate-400"><Lightbulb className="h-3 w-3" /> TruthLens supports critical reading; it does not replace it.</p>
    </div>
  )
}
