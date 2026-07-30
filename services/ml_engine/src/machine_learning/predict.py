"""
Tầng 5: Dự đoán (Inference).

Kiến trúc "Model-based Score Scaling":
    Dữ liệu → WoE Transform → XGBoost → PD → FICO Score
                   ↓
         WoE Contribution (giải thích từng biến theo công thức BA)

Ưu điểm so với Additive Scorecard thuần túy:
- AUC cao hơn Logistic Regression (XGBoost bắt được phi tuyến, tương tác biến)
- Vẫn có khả năng giải thích từng biến qua WoE Contribution
- Dải điểm FICO được hiệu chỉnh theo thông số Novabank (Target Score, Odds, PDO)
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

    # ── SCORECARD CALIBRATION ───────────────────────────────────────────────

    def _pd_to_credit_score(self, pd_value: float) -> int:
        """Chuyển đổi Xác suất Nợ xấu (PD) sang Điểm Tín dụng.

        Công thức FICO-style (chuẩn BIS 2004):
            Score = Target_Score - Factor × ln(Odds / Target_Odds)
            Factor = PDO / ln(2)

        Nguồn: BA Document - Novabank Credit Scorecard v1.0
        """
        target_score = self.scorecard_cfg.get("target_score", 500)
        target_odds  = self.scorecard_cfg.get("target_odds", 3.58)
        pdo          = self.scorecard_cfg.get("pdo", 50)
        score_min    = self.scorecard_cfg.get("score_min", 381)
        score_max    = self.scorecard_cfg.get("score_max", 553)

        pd_value = max(min(pd_value, 0.9999), 0.0001)
        odds     = pd_value / (1 - pd_value)
        factor   = pdo / math.log(2)
        score    = int(round(target_score - factor * math.log(odds / target_odds)))
        return max(min(score, score_max), score_min)

    def _assign_risk_tier(self, credit_score: int) -> tuple[str, str]:
        """Phân loại khách hàng vào nhóm rủi ro và đưa ra quyết định.

        Ngưỡng dựa trên phân phối điểm thực tế của tập huấn luyện Novabank:
            >= 510 : Rủi ro thấp   → Tự động phê duyệt
            467-509: Rủi ro trung bình thấp → Phê duyệt có điều kiện (lãi suất cao hơn)
            424-466: Rủi ro trung bình cao  → Thẩm định thủ công
            < 424  : Rủi ro cao    → Từ chối tự động
        """
        if credit_score >= 510:
            return "LOW", "APPROVED"
        elif credit_score >= 467:
            return "MEDIUM_LOW", "APPROVED_CONDITIONAL"
        elif credit_score >= 424:
            return "MEDIUM_HIGH", "MANUAL_REVIEW"
        else:
            return "HIGH", "REJECTED"

    # ── WoE CONTRIBUTION (EXPLAINABILITY) ───────────────────────────────────

    def _calculate_contributions(self, X_woe_row: pd.Series) -> dict:
        """Tính đóng góp điểm của từng biến theo công thức BA.

        Công thức: Points_i = Round(WoE_i × score_factor / 10)
        Nguồn: BA Document — Mục 4, Tính toán điểm

        Args:
            X_woe_row: Một hàng dữ liệu đã qua WoE transform.

        Returns:
            dict chứa điểm đóng góp của từng biến, ví dụ:
            {
                "loan_to_income_ratio": -12.5,   # đóng góp âm → tăng rủi ro
                "person_income":         8.2,    # đóng góp dương → giảm rủi ro
                ...
            }
        """
        score_factor = self.scorecard_cfg.get("score_factor", 72.13)
        all_feature_cols = self.config.get("numerical_cols", []) + self.config.get("categorical_cols", [])

        contributions = {}
        for col in all_feature_cols:
            if col in X_woe_row.index:
                woe_val = float(X_woe_row[col])
                points  = round(woe_val * score_factor / 10, 2)
                contributions[col] = points

        return contributions

    def _get_top_factors(self, contributions: dict, top_n: int = 3) -> dict:
        """Trích xuất top yếu tố tác động đến quyết định tín dụng.

        Returns:
            dict với 2 danh sách:
            - positive_factors: Top biến làm TĂNG điểm (có lợi cho khách hàng)
            - negative_factors: Top biến làm GIẢM điểm (rủi ro cao)
        """
        sorted_items = sorted(contributions.items(), key=lambda x: x[1], reverse=True)

        positive = [
            {"feature": k, "points": v}
            for k, v in sorted_items if v > 0
        ][:top_n]

        negative = [
            {"feature": k, "points": v}
            for k, v in sorted(contributions.items(), key=lambda x: x[1])
            if v < 0
        ][:top_n]

        return {
            "positive_factors": positive,   # Yếu tố bảo vệ (điểm tốt)
            "negative_factors": negative,   # Yếu tố rủi ro (điểm xấu)
        }

    # ── SCORING ─────────────────────────────────────────────────────────────

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
            risk_tier, decision = self._assign_risk_tier(credit_score)
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
        """Chấm điểm tín dụng cho một hồ sơ khách hàng đơn lẻ.

        Returns:
            dict gồm:
            - pd_score       : Xác suất nợ xấu (0.0 – 1.0)
            - credit_score   : Điểm tín dụng (381 – 553)
            - risk_tier      : Phân hạng rủi ro (LOW / MEDIUM_LOW / MEDIUM_HIGH / HIGH)
            - decision       : Quyết định tín dụng
            - contributions  : Điểm đóng góp của từng biến (giải thích AI)
            - top_factors    : Top yếu tố tích cực / tiêu cực
        """
        self._load_resources()

        df_single = pd.DataFrame([record])

        # WoE transform (cần trước khi đưa vào XGBoost VÀ để tính contribution)
        X_enc = self.feature_eng.transform(df_single)

        # Đảm bảo đủ cột
        if hasattr(self.model, "feature_names_in_"):
            expected_features = list(self.model.feature_names_in_)
            for col in expected_features:
                if col not in X_enc.columns:
                    X_enc[col] = 0.0
            X_enc_model = X_enc[expected_features]
        else:
            X_enc_model = X_enc

        # Dự đoán PD bằng XGBoost
        pd_val = float(self.model.predict_proba(X_enc_model)[0, 1])

        # Chuyển PD → Credit Score → Risk Tier
        credit_score = self._pd_to_credit_score(pd_val)
        risk_tier, decision = self._assign_risk_tier(credit_score)

        # Tính WoE Contribution cho từng biến (Explainability)
        contributions = self._calculate_contributions(X_enc.iloc[0])
        top_factors   = self._get_top_factors(contributions, top_n=3)

        return {
            "pd_score":     round(pd_val, 4),
            "credit_score": credit_score,
            "risk_tier":    risk_tier,
            "decision":     decision,
            "contributions": contributions,
            "top_factors":   top_factors,
        }
