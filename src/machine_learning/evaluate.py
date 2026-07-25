"""
evaluate.py — Tầng 4: Đánh giá Chất lượng Mô hình (Model Evaluation).
Tính toán Gini, KS, AUC-ROC và xuất biểu đồ/báo cáo.
"""
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score, roc_curve,
    classification_report
)

from src.machine_learning.config import METRICS_PATH, FIGURES_DIR

logger = logging.getLogger(__name__)


def gini_score(y_true: pd.Series, y_prob: np.ndarray) -> float:
    """Tính Gini Coefficient từ AUC: Gini = 2 * AUC - 1."""
    auc = roc_auc_score(y_true, y_prob)
    return 2 * auc - 1


def ks_score(y_true: pd.Series, y_prob: np.ndarray) -> float:
    """Tính KS Statistic (Kolmogorov–Smirnov)."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    return float(np.max(tpr - fpr))


def evaluate(model: XGBClassifier,
             X_test: pd.DataFrame,
             y_test: pd.Series,
             save: bool = True) -> dict:
    """Đánh giá đầy đủ mô hình trên tập Test và lưu báo cáo."""
    logger.info("Evaluating model performance...")

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    auc   = roc_auc_score(y_test, y_prob)
    gini  = gini_score(y_test, y_prob)
    ks    = ks_score(y_test, y_prob)

    metrics = {
        "auc":  round(float(auc),  4),
        "gini": round(float(gini), 4),
        "ks":   round(float(ks),   4),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }

    logger.info(f"  AUC-ROC : {metrics['auc']:.4f}")
    logger.info(f"  Gini    : {metrics['gini']:.4f}")
    logger.info(f"  KS Stat : {metrics['ks']:.4f}")

    if save:
        _save_metrics(metrics)
        _plot_roc_curve(y_test, y_prob)
        _plot_feature_importance(model)

    return metrics


def _save_metrics(metrics: dict) -> None:
    """Lưu dictionary chỉ số đánh giá ra file JSON."""
    Path(METRICS_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    logger.info(f"Metrics saved to: {METRICS_PATH}")


def _plot_roc_curve(y_true: pd.Series, y_prob: np.ndarray) -> None:
    """Vẽ đường cong ROC và lưu hình ảnh."""
    try:
        import matplotlib.pyplot as plt
        Path(FIGURES_DIR).mkdir(parents=True, exist_ok=True)

        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc = roc_auc_score(y_true, y_prob)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color="#2563EB", lw=2, label=f"ROC Curve (AUC = {auc:.4f})")
        plt.plot([0, 1], [0, 1], "k--", lw=1, label="Random Classifier")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve — Credit Risk Model")
        plt.legend(loc="lower right")
        plt.tight_layout()
        output_path = Path(FIGURES_DIR) / "roc_curve.png"
        plt.savefig(output_path, dpi=150)
        plt.close()
        logger.info(f"ROC Curve saved to: {output_path}")
    except Exception as e:
        logger.warning(f"Could not plot ROC curve: {e}")


def _plot_feature_importance(model: XGBClassifier) -> None:
    """Vẽ biểu đồ Feature Importance và lưu hình ảnh."""
    try:
        import matplotlib.pyplot as plt
        Path(FIGURES_DIR).mkdir(parents=True, exist_ok=True)

        importance = pd.Series(
            model.feature_importances_,
            index=model.feature_names_in_
        ).sort_values(ascending=True).tail(20)

        plt.figure(figsize=(10, 8))
        importance.plot(kind="barh", color="#2563EB")
        plt.title("Top 20 Feature Importances — XGBoost")
        plt.xlabel("Importance Score")
        plt.tight_layout()
        output_path = Path(FIGURES_DIR) / "feature_importance.png"
        plt.savefig(output_path, dpi=150)
        plt.close()
        logger.info(f"Feature Importance chart saved to: {output_path}")
    except Exception as e:
        logger.warning(f"Could not plot feature importance: {e}")
