"""
Tầng 4: Đánh giá Chất lượng Mô hình (Model Evaluation).
"""
from typing import Any
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.metrics import (
    roc_auc_score, roc_curve,
    classification_report,
    brier_score_loss, log_loss
)

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Class đánh giá mô hình và tính toán Metrics (Không lưu ảnh tĩnh)."""
    
    def __init__(self, config: dict):
        """Khởi tạo với cấu hình bài toán."""
        self.config = config
        self.metrics_path = self.config.get("metrics_output_abs")
        self.task_name = self.config.get("task_name", "Unknown Task")

    def evaluate(self, model: Any,
                 X_test: pd.DataFrame,
                 y_test: pd.Series,
                 save: bool = True) -> dict:
        """Đánh giá mô hình và đóng gói toàn bộ Data phục vụ trực quan hóa vào JSON."""
        logger.info(f"Evaluating model performance and probability calibration for task: {self.task_name}...")

        # 1. Lấy xác suất dự đoán (PD) và nhãn phân lớp
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        # 2. Chỉ số phân loại truyền thống (Discrimination)
        auc = float(roc_auc_score(y_test, y_prob))
        gini = 2.0 * auc - 1.0

        # 3. Chỉ số hiệu chuẩn xác suất (Probability Calibration Metrics)
        brier = float(brier_score_loss(y_test, y_prob))
        lloss = float(log_loss(y_test, y_prob))

        # Tính toán roc_curve 1 lần duy nhất cho cả KS Statistic và đồ thị ROC
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        ks = float(np.max(tpr - fpr))

        # Trích xuất dữ liệu Feature Importance (hỗ trợ cả base XGBoost và CalibratedClassifierCV)
        base_estimator = getattr(model, "estimator", model)
        if hasattr(base_estimator, "feature_names_in_") and hasattr(base_estimator, "feature_importances_"):
            feature_importance = dict(zip(
                base_estimator.feature_names_in_, 
                [float(x) for x in base_estimator.feature_importances_]
            ))
        elif hasattr(model, "feature_names_in_") and hasattr(model, "feature_importances_"):
            feature_importance = dict(zip(
                model.feature_names_in_, 
                [float(x) for x in model.feature_importances_]
            ))
        else:
            feature_importance = {}

        metrics = {
            "auc":         round(auc, 4),
            "gini":        round(gini, 4),
            "ks":          round(ks, 4),
            "brier_score": round(brier, 4),
            "log_loss":    round(lloss, 4),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "roc_curve_data": {
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist()
            },
            "feature_importance": feature_importance
        }

        logger.info(f"  AUC-ROC    : {metrics['auc']:.4f}")
        logger.info(f"  Gini       : {metrics['gini']:.4f}")
        logger.info(f"  KS Stat    : {metrics['ks']:.4f}")
        logger.info(f"  Brier Score: {metrics['brier_score']:.4f}")
        logger.info(f"  Log Loss   : {metrics['log_loss']:.4f}")

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

