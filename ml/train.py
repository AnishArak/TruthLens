"""Train and evaluate the three TruthLens classifiers.

Usage (from the project root, venv active):
    python ml/train.py
    python ml/train.py --sample 5000      # quick smoke run on a subset

Outputs:
    ml/saved_models/best_model.joblib   best pipeline (TF-IDF + classifier), chosen by F1
    ml/saved_models/metrics.json        real metrics for ALL three models on the held-out test set
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocessing import clean_text  # noqa: E402
from evaluation import evaluate_model  # noqa: E402

ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "dataset"
MODEL_DIR = ROOT / "saved_models"
SEED = 42  # reproducible split and model initialisation


def load_dataset(sample=None, data_dir=DATASET_DIR):
    fake_path, true_path = Path(data_dir) / "Fake.csv", Path(data_dir) / "True.csv"
    if not fake_path.exists() or not true_path.exists():
        sys.exit(f"Dataset not found. Place Fake.csv and True.csv in {data_dir}\n"
                 "Download: https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset")
    fake = pd.read_csv(fake_path)
    real = pd.read_csv(true_path)
    fake["label"] = 1   # 1 = FAKE
    real["label"] = 0   # 0 = REAL
    df = pd.concat([fake, real], ignore_index=True)
    print(f"Loaded {len(df)} rows ({len(fake)} fake, {len(real)} real)")

    # Missing values and duplicates
    df["title"] = df["title"].fillna("")
    df["text"] = df["text"].fillna("")
    df = df[(df["title"].str.strip() + df["text"].str.strip()) != ""]
    before = len(df)
    df = df.drop_duplicates(subset=["title", "text"])
    # A text can appear under both labels; keep neither to avoid contradictory supervision.
    dup_text = df.duplicated(subset=["text"], keep=False) & df["text"].str.strip().ne("")
    conflicts = df[dup_text].groupby("text")["label"].nunique()
    conflict_texts = set(conflicts[conflicts > 1].index)
    df = df[~df["text"].isin(conflict_texts)]
    print(f"After cleaning: {len(df)} rows (removed {before - len(df)} duplicates/conflicts)")

    if sample:
        df = df.groupby("label", group_keys=False).apply(
            lambda g: g.sample(min(len(g), sample // 2), random_state=SEED))
        print(f"Using a stratified sample of {len(df)} rows")

    # Combine headline and body, then normalise (lowercase, stopwords, tokenization)
    df["content"] = (df["title"] + " " + df["text"]).map(clean_text)
    df = df[df["content"].str.len() > 0]
    return df[["content", "label"]]


def build_models():
    """Three classifiers; each is wrapped in a Pipeline so TF-IDF is fit on training data only."""
    def tfidf():
        return TfidfVectorizer(max_features=50000, ngram_range=(1, 2), min_df=3, max_df=0.9, sublinear_tf=True)

    return {
        "Logistic Regression": Pipeline([("tfidf", tfidf()),
                                         ("clf", LogisticRegression(max_iter=1000, random_state=SEED))]),
        "Multinomial Naive Bayes": Pipeline([("tfidf", tfidf()), ("clf", MultinomialNB())]),
        # LinearSVC has no predict_proba; calibration gives probability-like scores for confidence/LIME.
        "Linear SVM": Pipeline([("tfidf", tfidf()),
                                ("clf", CalibratedClassifierCV(LinearSVC(random_state=SEED), cv=3))]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None, help="use a stratified subset of N rows (smoke test)")
    ap.add_argument("--data-dir", default=str(DATASET_DIR), help="folder containing Fake.csv and True.csv")
    ap.add_argument("--model-dir", default=str(MODEL_DIR), help="where to save the model and metrics")
    args = ap.parse_args()
    model_dir = Path(args.model_dir)

    df = load_dataset(args.sample, args.data_dir)
    # 80/20 stratified split with fixed seed
    X_train, X_test, y_train, y_test = train_test_split(
        df["content"], df["label"], test_size=0.2, random_state=SEED, stratify=df["label"])
    print(f"Train: {len(X_train)}  Test: {len(X_test)}")

    results, fitted = [], {}
    for name, pipe in build_models().items():
        print(f"Training {name} ...")
        t0 = time.time()
        pipe.fit(X_train, y_train)          # TF-IDF vocabulary learned from training data only
        secs = round(time.time() - t0, 2)
        res = evaluate_model(name, pipe, X_test, y_test, secs)
        print(f"  accuracy={res['accuracy']:.4f} precision={res['precision']:.4f} "
              f"recall={res['recall']:.4f} f1={res['f1']:.4f}")
        results.append(res)
        fitted[name] = pipe

    best = max(results, key=lambda r: r["f1"])
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": fitted[best["name"]], "model_name": best["name"]}, model_dir / "best_model.joblib")

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "dataset": "Kaggle Fake and Real News Dataset (Fake.csv + True.csv)",
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
        "sampled_run": bool(args.sample),
        "best_model": best["name"],
        "selection_criterion": "highest F1-score on held-out test set",
        "models": results,
    }
    (model_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nBest model: {best['name']} (F1={best['f1']:.4f}). Saved to {model_dir}")


if __name__ == "__main__":
    main()
