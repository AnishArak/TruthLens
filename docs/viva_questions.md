# TruthLens — Viva Questions and Answers

**1. What does TruthLens do?**
It classifies news text as REAL/FAKE with an ML model, explains the prediction (LIME), analyses sentiment and clickbait, extracts claims, retrieves evidence when a search provider is configured, and assesses the publisher — reporting these as separate outcomes.

**2. Does the classifier verify facts?**
No. It learns statistical writing-style patterns from its training data. Fact verification needs external evidence, which is why evidence verification is a separate module.

**3. Why not combine everything into one score?**
A single number would imply false certainty and mix unlike things (style probability, retrieved evidence, publisher reputation). Separate outcomes are more honest and easier to interpret.

**4. What does "confidence" mean here?**
The model's predicted probability for its chosen class. It reflects similarity to training patterns, not the chance the story is true.

**5. What is TF-IDF?**
Term Frequency × Inverse Document Frequency: words frequent in a document but rare across the corpus get higher weight. We use unigrams+bigrams with sublinear TF.

**6. Why fit TF-IDF only on the training data?**
Fitting on all data lets test-set vocabulary and IDF statistics leak into training, inflating metrics. Putting TF-IDF in a `Pipeline` fit on the training split prevents this.

**7. Explain Logistic Regression.**
A linear model applying a sigmoid to wᵀx+b to give P(FAKE|x), trained by minimising regularised log-loss. Coefficients are interpretable.

**8. Explain Multinomial Naive Bayes.**
Applies Bayes' theorem assuming terms are conditionally independent given the class, using word counts/TF-IDF. Fast, strong baseline for text.

**9. Explain Linear SVM and why calibration is used.**
It finds the maximum-margin separating hyperplane. LinearSVC has no `predict_proba`, so `CalibratedClassifierCV` is used to obtain probabilities for confidence and LIME.

**10. How is the best model selected?**
Highest F1-score (FAKE as positive class) on the held-out 20% test split; metrics for all three are saved to `metrics.json`.

**11. Why F1 and not just accuracy?**
F1 balances precision and recall and is more informative when classes or error costs differ.

**12. What are precision and recall here?**
Precision = of articles predicted FAKE, the fraction truly FAKE. Recall = of truly FAKE articles, the fraction found.

**13. What is a confusion matrix?**
A table of actual vs predicted classes (TN, FP, FN, TP) showing the types of errors.

**14. Why stratified split and a fixed seed?**
Stratification keeps the class ratio equal in train and test; a fixed seed (42) makes results reproducible.

**15. Which preprocessing steps are implemented? Is lemmatization used?**
Lower-casing, URL/HTML/dateline removal, tokenization, stopword removal. Stemming (Porter) exists as an option but is off by default; lemmatization is not implemented, so it must not be claimed.

**16. Why remove news-agency datelines?**
"WASHINGTON (Reuters) -" appears almost only in the REAL class, so the model could learn the publisher instead of content (dataset artefact).

**17. Why can accuracy be ~99% on this dataset yet poor in the real world?**
The two classes differ in source style and topic period. High scores can reflect these artefacts. Cross-dataset testing is needed to estimate real-world performance.

**18. How does LIME work?**
It perturbs the input (removing words), observes the model's predictions, and fits a weighted linear model around that instance; coefficients show which words pushed toward REAL or FAKE locally.

**19. Limitations of LIME?**
Local only, depends on random sampling (we fix the seed), word-level so ignores context, and reflects correlation learned by the model — not why something is true.

**20. How does evidence verification work?**
Extract check-worthy claims → build queries → fetch results from a provider → compute similarity (Sentence-Transformers or TF-IDF fallback) → apply a negation-cue stance heuristic → aggregate to Supporting / Contradicting / Mixed / Insufficient.

**21. What happens without a search API key?**
The module returns "Evidence retrieval unavailable" with the reason. Nothing is invented.

**22. Is the supporting/contradicting label reliable?**
It is a simple heuristic, not natural-language inference, and the UI says so. A future improvement is an NLI model.

**23. Why is the clickbait detector rule-based?**
It is a transparent baseline (phrase list, caps, punctuation, listicle pattern) whose scoring is fully visible. It is not a trained classifier, and sensational wording doesn't imply fakeness.

**24. How does VADER work?**
A valence lexicon with rules for negation, intensifiers and punctuation; compound score ≥0.05 positive, ≤−0.05 negative, otherwise neutral.

**25. How is SSRF prevented in URL analysis?**
Only http/https; hostnames resolved and every IP must be public (no loopback/private/link-local); redirects re-validated each hop; size cap, timeouts, text-only parsing, robots.txt respected.

**26. Why is an unknown domain not labelled fake?**
Absence from a small database says nothing about reliability; labelling it fake would be a false claim.

**27. What if MongoDB is down?**
Analysis still works; the response says it wasn't saved; history is disabled (503) and the dashboard shows zeros with the DB status.

**28. What is stored in MongoDB and why only an excerpt?**
Headline, 500-char excerpt, prediction, confidence, features and evidence references. Full article text isn't stored for privacy.

**29. How would you improve the system?**
Transformer (BERT) classifier, NLI-based stance, fact-check database integration, cross-domain/temporal evaluation, multilingual support.

**30. How do you ensure no metrics are fabricated?**
Metrics are computed by `evaluation.py` from real test predictions, written to `metrics.json` and read by the API; the UI shows an empty state if no training has happened.
