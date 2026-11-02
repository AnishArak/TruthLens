# TruthLens: An AI-Powered Fake News Detection and Verification Platform

> Result fields marked **«TO FILL»** must be populated from your own run of `python ml/train.py`
> (see `ml/saved_models/metrics.json` or the Model Performance page). No experimental numbers are invented here.

## 1. Abstract
Online misinformation spreads quickly and is hard to assess at scale. TruthLens is a web platform that combines natural
language processing, supervised machine learning, explainable AI and evidence retrieval to support critical reading of
news. Three classifiers (Logistic Regression, Multinomial Naive Bayes, Linear SVM) are trained on TF-IDF features from the
Kaggle Fake and Real News dataset and the best model by F1-score is deployed. LIME explains individual predictions;
rule-based clickbait detection and VADER sentiment add stylistic signals; a modular evidence engine compares extracted
claims to retrieved sources; and a source module reports publisher information. The system reports classifier output,
evidence verification and source assessment as separate results because a text classifier cannot verify facts.
Results: **«TO FILL: best model, accuracy, precision, recall, F1»**.

## 2. Introduction
Social media and messaging platforms let unverified content reach large audiences. Manual fact-checking is accurate but
slow, so automated assistance is attractive provided its limits are understood. TruthLens is designed as a decision-support
tool rather than an arbiter of truth.

## 3. Problem statement
Readers lack accessible tools that (a) flag suspicious writing patterns, (b) explain why, (c) surface independent evidence and
(d) show publisher context — while being honest about uncertainty.

## 4. Objectives
1. Classify articles as REAL or FAKE with a trained model and report model confidence.
2. Explain predictions at word level using LIME.
3. Extract claims and retrieve supporting/contradicting evidence through a pluggable search provider.
4. Detect sensational language and analyse sentiment.
5. Assess publisher identity and reputation without labelling unknown domains fake.
6. Store history and show analytics; evaluate models with real held-out metrics.

## 5. Existing system
Manual fact-checking organisations (Snopes, PolitiFact, Alt News, BOOM, etc.) provide high-quality verdicts for selected claims
but do not cover all content. Many academic detectors output only a label with no explanation, evidence or source context, and
are often presented as if they establish truth.

## 6. Proposed system
A full-stack application: React frontend, Flask REST backend, scikit-learn/NLTK/LIME/VADER ML-NLP layer, MongoDB persistence,
and an evidence module. Key principle: **separate outcomes** (classification / evidence / source) with explicit "unavailable"
states instead of fabricated output.

## 7. Literature review
*(Verify each citation's details against the original source before submission.)*
- Shu et al. (2017) survey fake-news detection on social media from a data-mining perspective, covering content- and
  social-context features.
- Ahmed, Traore and Saad (2017) evaluate n-gram features with several classifiers (including linear SVM) for fake-news detection.
- Vosoughi, Roy and Aral (2018) show that false news diffused farther and faster than true news on Twitter.
- Ribeiro, Singh and Guestrin (2016) introduce LIME for local, model-agnostic explanations.
- Hutto and Gilbert (2014) present VADER for social-media sentiment.
- Reimers and Gurevych (2019) present Sentence-BERT for semantic similarity.
- Devlin et al. (2019) present BERT, a basis for stronger transformer classifiers (future work here).
- A recurring finding in the literature is that models trained on one dataset generalise poorly to other domains and time periods.

## 8. NLP methodology
Implemented preprocessing: lower-casing → removal of URLs, HTML and agency datelines → regex tokenization → stopword removal.
**Stemming and lemmatization are optional and not applied by default.** Features: TF-IDF unigrams+bigrams (max 50,000 features,
min_df=3, max_df=0.9, sublinear TF). Additional NLP: keyword/bigram extraction, VADER sentiment, rule-based clickbait score,
heuristic claim extraction, semantic similarity (Sentence-Transformers or labelled TF-IDF fallback).

## 9. Dataset description
Kaggle *Fake and Real News Dataset* (`Fake.csv`, `True.csv`; columns title, text, subject, date). Label 1 = FAKE, 0 = REAL.
Cleaning: missing values filled, empty rows dropped, duplicate and label-conflicting articles removed, title+text combined.
Counts after cleaning: **«TO FILL from training log»**. Caveat: real articles are largely Reuters-style and fake articles come from
other outlets, producing source-style artefacts (mitigated, not eliminated, by dateline removal).

## 10. System architecture
See `docs/architecture.md`.

## 11. Algorithms
- **TF-IDF**: tf(t,d)·idf(t) with sublinear tf and L2 normalisation.
- **Logistic Regression**: P(y=1|x)=σ(wᵀx+b), trained by regularised log-loss minimisation.
- **Multinomial Naive Bayes**: P(y|x) ∝ P(y)·∏P(t|y)^{x_t}.
- **Linear SVM**: maximum-margin hyperplane; wrapped in `CalibratedClassifierCV` for probability estimates.
- **LIME**: perturbs the text by removing words, queries the model, fits a weighted linear surrogate; weights = local contributions.
- **VADER**: lexicon + rules for negation/intensifiers; compound score in [−1, 1] (≥0.05 positive, ≤−0.05 negative).
- **Cosine similarity** between claim and evidence embeddings/vectors.

## 12. Implementation
Python 3 / Flask backend; React 18 + Vite + Tailwind frontend; PyMongo; BeautifulSoup. SSRF-safe URL fetching (public-IP check on every
hop, size cap, timeouts, robots.txt). 34 automated backend tests (units + API with an in-memory store).

## 13. Results and evaluation
Protocol: stratified 80/20 split, seed 42, TF-IDF fit on training data only, metrics on the held-out test set (positive class = FAKE).

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Logistic Regression | «TO FILL» | «TO FILL» | «TO FILL» | «TO FILL» |
| Multinomial Naive Bayes | «TO FILL» | «TO FILL» | «TO FILL» | «TO FILL» |
| Linear SVM | «TO FILL» | «TO FILL» | «TO FILL» | «TO FILL» |

Best model (by F1): **«TO FILL»**. Confusion matrix and classification report: **«TO FILL — screenshot of Model Performance page»**.
Discuss: very high scores on this dataset usually reflect dataset artefacts, not real-world ability; recommend cross-dataset testing.

## 14. Advantages
Transparent and modular; explanation, evidence and source context in one tool; honest unavailable states; graceful degradation without
MongoDB or search keys; reproducible training; SSRF-hardened URL ingestion.

## 15. Limitations
- Classifier detects style patterns of one dataset (2016–2017, mostly US politics), not truth; generalisation is uncertain.
- Confidence is not the probability a story is true.
- LIME is local and correlational; word-level explanations can be unstable.
- Evidence stance uses a negation-cue heuristic, not NLI; retrieval quality depends on the provider and snippets.
- Clickbait detection is rule-based; sensational language does not imply falsehood.
- Source database is small and editable; unlisted ≠ unreliable.
- English only; no authentication; no multimedia analysis.

## 16. Future scope
Fine-tuned transformer classifier; NLI-based stance; integration with fact-check claim databases; cross-dataset and temporal evaluation;
multilingual support; user accounts; browser extension; image/video provenance checks.

## 17. Conclusion
TruthLens demonstrates an end-to-end, explainable and honest approach to assisting news verification. Its main contribution is the
separation of statistical classification from evidence-based verification and source assessment. **«TO FILL: one-paragraph summary of your measured results.»**

## 18. References
1. K. Shu, A. Sliva, S. Wang, J. Tang, H. Liu. "Fake News Detection on Social Media: A Data Mining Perspective." *ACM SIGKDD Explorations*, 2017.
2. H. Ahmed, I. Traore, S. Saad. "Detection of Online Fake News Using N-Gram Analysis and Machine Learning Techniques." *ISDDC*, 2017.
3. S. Vosoughi, D. Roy, S. Aral. "The spread of true and false news online." *Science*, 359(6380), 2018.
4. M. T. Ribeiro, S. Singh, C. Guestrin. "'Why Should I Trust You?': Explaining the Predictions of Any Classifier." *KDD*, 2016.
5. C. Hutto, E. Gilbert. "VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text." *ICWSM*, 2014.
6. N. Reimers, I. Gurevych. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." *EMNLP-IJCNLP*, 2019.
7. J. Devlin, M.-W. Chang, K. Lee, K. Toutanova. "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding." *NAACL*, 2019.
8. F. Pedregosa et al. "Scikit-learn: Machine Learning in Python." *JMLR*, 12, 2011.
9. C. Bisaillon. "Fake and Real News Dataset." Kaggle. https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset
