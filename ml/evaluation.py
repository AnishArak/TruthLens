"""Model evaluation helpers. All numbers are computed from real predictions on the held-out test set."""
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support,
                             confusion_matrix, classification_report)

LABELS = [0, 1]            # 0 = REAL, 1 = FAKE
LABEL_NAMES = ["REAL", "FAKE"]


def evaluate_model(name, model, X_test, y_test, train_seconds=None):
    y_pred = model.predict(X_test)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="binary", pos_label=1, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=LABELS)
    report = classification_report(y_test, y_pred, labels=LABELS, target_names=LABEL_NAMES,
                                   output_dict=True, zero_division=0)
    return {
        "name": name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision),   # for the FAKE (positive) class
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": cm.tolist(),  # rows = actual [REAL, FAKE], cols = predicted [REAL, FAKE]
        "labels": LABEL_NAMES,
        "classification_report": report,
        "test_size": int(len(y_test)),
        "train_seconds": train_seconds,
    }
