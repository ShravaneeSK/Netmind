"""Train and evaluate the NetMind models on a labelled dataset.

Fault classifier: Random Forest and XGBoost (plus a most-frequent baseline).
Anomaly detector: Isolation Forest trained on normal readings only.

Split: for each class, the first 70% of its readings (by time) train the model and the
last 30% test it, so test readings come from later than training readings.

Scores on simulated data only show that the code works. Never report them.
"""
import argparse
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             classification_report, f1_score, roc_auc_score)
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
NON_FEATURES = ["id", "received_at", "device_id", "fault_label",
                "packet_matched", "packet_gap_s", "session"]


def blocked_split(df, test_fraction):
    """Per class: earlier readings train, the latest readings test."""
    df = df.sort_values("received_at")
    test_idx = []
    for _, g in df.groupby("fault_label"):
        n_test = max(1, int(round(len(g) * test_fraction)))
        test_idx.extend(g.index[-n_test:])
    return df.drop(index=test_idx), df.loc[test_idx]


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate NetMind models")
    parser.add_argument("--data", default=str(ROOT / "ml" / "data" / "sim_dataset.csv"))
    parser.add_argument("--prefix", default="sim", help="prefix for saved model and report files")
    parser.add_argument("--test-fraction", type=float, default=0.3)
    args = parser.parse_args()

    models_dir = ROOT / "ml" / "models"
    reports_dir = ROOT / "ml" / "reports"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data)
    df["received_at"] = pd.to_datetime(df["received_at"], utc=True, format="ISO8601")
    features = [c for c in df.columns if c not in NON_FEATURES]

    train, test = blocked_split(df, args.test_fraction)
    print(f"Features: {len(features)}   train rows: {len(train)}   test rows: {len(test)}")

    le = LabelEncoder().fit(df["fault_label"])
    classes = list(le.classes_)
    X_train, X_test = train[features], test[features]
    y_train = le.transform(train["fault_label"])
    y_test = le.transform(test["fault_label"])

    models = {
        "baseline (most frequent)": DummyClassifier(strategy="most_frequent"),
        "random_forest": RandomForestClassifier(
            n_estimators=300, class_weight="balanced", random_state=0, n_jobs=-1),
        "xgboost": XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.1,
            random_state=0, eval_metric="mlogloss"),
    }

    rows, preds = [], {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        preds[name] = pred
        rows.append({
            "model": name,
            "accuracy": round(accuracy_score(y_test, pred), 3),
            "macro_f1": round(f1_score(y_test, pred, average="macro"), 3),
        })

    print("\n== Fault classifier: test results ==")
    print(pd.DataFrame(rows).to_string(index=False))

    for name in ("random_forest", "xgboost"):
        print(f"\n== {name}: per-class report ==")
        print(classification_report(y_test, preds[name], target_names=classes, digits=2))

    fig, ax = plt.subplots(figsize=(9, 8))
    ConfusionMatrixDisplay.from_predictions(
        y_test, preds["random_forest"], display_labels=classes,
        xticks_rotation=45, ax=ax, colorbar=False)
    plt.tight_layout()
    cm_path = reports_dir / f"{args.prefix}_confusion_rf.png"
    fig.savefig(cm_path, dpi=120)
    print(f"\nConfusion matrix saved to {cm_path}")

    rf = models["random_forest"]
    importance = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
    print("\n== Random Forest: top 10 features ==")
    print(importance.head(10).round(3).to_string())

    # Anomaly detector: learns only what 'normal' looks like
    normal_train = X_train[train["fault_label"].values == "normal"]
    iso = IsolationForest(n_estimators=300, random_state=0).fit(normal_train)
    threshold = float(np.percentile(iso.decision_function(normal_train), 5))
    scores = iso.decision_function(X_test)
    flagged = scores < threshold
    is_fault = (test["fault_label"] != "normal").values

    print("\n== Anomaly detector (Isolation Forest, trained on normal only) ==")
    print(f"normal training rows: {len(normal_train)}")
    print(f"ROC AUC, normal vs any fault: {roc_auc_score(is_fault, -scores):.3f}")
    print(f"false alarms on normal test rows: {flagged[~is_fault].mean():.0%} "
          f"({int(flagged[~is_fault].sum())} of {int((~is_fault).sum())})")
    print("share of test rows flagged, per class:")
    by_class = pd.Series(flagged, index=test.index).groupby(test["fault_label"]).mean()
    print(by_class.round(2).to_string())

    joblib.dump({"model": models["random_forest"], "features": features, "classes": classes},
                models_dir / f"{args.prefix}_fault_rf.joblib")
    joblib.dump({"model": models["xgboost"], "features": features, "classes": classes},
                models_dir / f"{args.prefix}_fault_xgb.joblib")
    joblib.dump({"model": iso, "features": features, "threshold": threshold},
                models_dir / f"{args.prefix}_anomaly_if.joblib")
    print(f"\nModels saved in {models_dir}")


if __name__ == "__main__":
    main()
