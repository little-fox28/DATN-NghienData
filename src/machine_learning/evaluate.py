"""
Tầng 4: Đánh giá Chất lượng Mô hình (Model Evaluation).
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

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Class đánh giá mô hình và tính toán Metrics (Không lưu ảnh tĩnh)."""
    
    def __init__(self, config: dict):
        """Khởi tạo với cấu hình bài toán."""
        self.config = config
        self.metrics_path = self.config.get("metrics_output_abs")
        self.task_name = self.config.get("task_name", "Unknown Task")

    def _gini_score(self, y_true: pd.Series, y_prob: np.ndarray) -> float:
        """Tính Gini Coefficient từ AUC: Gini = 2 * AUC - 1."""
        auc = roc_auc_score(y_true, y_prob)
        return 2 * auc - 1

    def _ks_score(self, y_true: pd.Series, y_prob: np.ndarray) -> float:
        """Tính KS Statistic (Kolmogorov–Smirnov)."""
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        return float(np.max(tpr - fpr))

    def evaluate(self, model: XGBClassifier,
                 X_test: pd.DataFrame,
                 y_test: pd.Series,
                 save: bool = True) -> dict:
        """Đánh giá mô hình và đóng gói toàn bộ Data phục vụ trực quan hóa vào JSON."""
        logger.info(f"Evaluating model performance for task: {self.task_name}...")

        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        auc   = roc_auc_score(y_test, y_prob)
        gini  = self._gini_score(y_test, y_prob)
        ks    = self._ks_score(y_test, y_prob)

        # 1. Trích xuất dữ liệu vẽ đường ROC
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        
        # 2. Trích xuất dữ liệu Feature Importance
        if hasattr(model, "feature_names_in_"):
            feature_importance = dict(zip(
                model.feature_names_in_, 
                [float(x) for x in model.feature_importances_]
            ))
        else:
            feature_importance = {}

        metrics = {
            "auc":  round(float(auc),  4),
            "gini": round(float(gini), 4),
            "ks":   round(float(ks),   4),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "roc_curve_data": {
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist()
            },
            "feature_importance": feature_importance
        }

        logger.info(f"  AUC-ROC : {metrics['auc']:.4f}")
        logger.info(f"  Gini    : {metrics['gini']:.4f}")
        logger.info(f"  KS Stat : {metrics['ks']:.4f}")

        if save:
            self._save_metrics(metrics)

        return metrics

    def _save_metrics(self, metrics: dict) -> None:
        """Lưu toàn bộ chỉ số và dữ liệu biểu đồ ra file JSON."""
        path_obj = Path(self.metrics_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(path_obj, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4, ensure_ascii=False)
        logger.info(f"Metrics & Visualization Data saved to: {self.metrics_path}")

