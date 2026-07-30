"""
Tầng 5: Dự đoán (Inference).
"""
import math
import logging
import numpy as np
import pandas as pd

from services.ml_engine.src.machine_learning.features import FeatureEngineer
from services.ml_engine.src.machine_learning.train import ModelTrainer

logger = logging.getLogger(__name__)

class ModelPredictor:
    """Class đảm nhiệm việc dự đoán, chấm điểm tín dụng dựa trên mô hình đã huấn luyện."""
    
    def __init__(self, config: dict):
        """Khởi tạo với cấu hình bài toán."""
        self.config = config
        self.scorecard_cfg = self.config.get("scorecard", {})
        
        # Sử dụng lại các class đã refactor để load model và encoder
        self.feature_eng = FeatureEngineer(self.config)
        self.trainer = ModelTrainer(self.config)
        
        # Biến lưu trữ sau khi load
        self.encoder = None
        self.model = None

    def _load_resources(self):
        """Tải mô hình và encoder vào bộ nhớ nếu chưa có."""
        if self.encoder is None:
            self.encoder = self.feature_eng.load_encoder()
        if self.model is None:
            self.model = self.trainer.load_model()

    def _pd_to_credit_score(self, pd_value: float) -> int:
        """Chuyển đổi Xác suất Nợ xấu (PD) sang Điểm Tín dụng (300 - 850)."""
        target_score = self.scorecard_cfg.get("target_score", 600)
        target_odds  = self.scorecard_cfg.get("target_odds", 50)
        pdo          = self.scorecard_cfg.get("pdo", 20)

        pd_value = max(min(pd_value, 0.9999), 0.0001)
        odds  = pd_value / (1 - pd_value)
        factor = pdo / math.log(2)
        score = int(round(target_score - factor * math.log(odds / target_odds)))
        return max(min(score, 850), 300)

    def _assign_risk_tier(self, pd_value: float) -> tuple[str, str]:
        """Phân loại khách hàng vào nhóm rủi ro và đưa ra quyết định."""
        if pd_value < 0.10:
            return "LOW", "APPROVED"
        elif pd_value < 0.25:
            return "MEDIUM", "APPROVED"
        elif pd_value < 0.40:
            return "HIGH", "MANUAL_REVIEW"
        else:
            return "CRITICAL", "REJECTED"

    def score_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chấm điểm tín dụng cho một batch khách hàng."""
        logger.info(f"Scoring {len(df):,} records...")
        
        self._load_resources()

        X_enc = self.feature_eng.transform(df)

        # Đảm bảo đủ tất cả các cột mà model yêu cầu
        if hasattr(self.model, "feature_names_in_"):
            expected_features = list(self.model.feature_names_in_)
            for col in expected_features:
                if col not in X_enc.columns:
                    X_enc[col] = 0.0
            X_enc = X_enc[expected_features]

        y_prob = self.model.predict_proba(X_enc)[:, 1]

        results = []
        for pd_val in y_prob:
            credit_score = self._pd_to_credit_score(pd_val)
            risk_tier, decision = self._assign_risk_tier(pd_val)
            results.append({
                "pd_score":     round(float(pd_val), 4),
                "credit_score": credit_score,
                "risk_tier":    risk_tier,
                "decision":     decision,
            })

        result_df = pd.DataFrame(results)
        logger.info("Scoring complete.")
        return pd.concat([df.reset_index(drop=True), result_df], axis=1)

    def score_single(self, record: dict) -> dict:
        """Chấm điểm tín dụng cho một hồ sơ khách hàng đơn lẻ."""
        df = pd.DataFrame([record])
        result = self.score_batch(df)
        return result[["pd_score", "credit_score", "risk_tier", "decision"]].iloc[0].to_dict()

