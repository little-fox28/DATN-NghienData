"""
Tầng 5: Dự đoán (Inference).

Kiến trúc "Model-based Score Scaling":
    Dữ liệu → WoE Transform → XGBoost → PD → FICO Score
                   ↓                          ↓
         WoE Contribution              Risk-Based Pricing Engine
         (giải thích từng biến)        (APR + Limit + PMT Simulation)

Ưu điểm so với Additive Scorecard thuần túy:
- AUC cao hơn Logistic Regression (XGBoost bắt được phi tuyến, tương tác biến)
- Vẫn có khả năng giải thích từng biến qua WoE Contribution
- Dải điểm FICO được hiệu chỉnh theo thông số Novabank (Target Score, Odds, PDO)
- Lãi suất cá nhân hóa theo Risk-Based Pricing (SPEC-ML-PRICING-2026-V1.0)
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
        self.pricing_cfg   = self.config.get("pricing_policy", {})

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
        """Chuyển đổi Xác suất Nợ xấu (PD) sang Điểm Tín dụng chuẩn FICO (300 – 850).
        
        Công thức FICO-style (chuẩn nội suy tỷ lệ cược An toàn):
        Odds = (1 - PD) / PD
        Offset = Target_Score - Factor * ln(Target_Odds)
        Score = Offset + Factor * ln(Odds)
        """
        import math
        
        target_score = self.scorecard_cfg.get("target_score", 600)
        target_odds  = self.scorecard_cfg.get("target_odds", 20)
        pdo          = self.scorecard_cfg.get("pdo", 20)
        score_min    = self.scorecard_cfg.get("score_min", 300)
        score_max    = self.scorecard_cfg.get("score_max", 850)

        # Xử lý an toàn cận biên (Safe Math)
        pd_value = max(min(pd_value, 1.0 - 1e-9), 1e-9)
        
        # Đảo trục logic sang tỷ lệ Good/Bad
        odds_good_bad = (1.0 - pd_value) / pd_value
        factor        = pdo / math.log(2)
        
        # Tính toán điểm nội suy với Base Offset
        offset = target_score - (factor * math.log(target_odds))
        score  = int(round(offset + factor * math.log(odds_good_bad)))
        
        return max(min(score, score_max), score_min)

    def _assign_risk_tier(self, credit_score: int) -> tuple[str, str]:
        """Phân loại khách hàng vào nhóm rủi ro và đưa ra quyết định tín dụng.

        Quy tắc phân tầng FICO cập nhật (hỗ trợ Buffer Zone / Gray Zone):
            >= 740 : Very Good / Exceptional     → Tự động phê duyệt (APPROVED)
            670-739: Good                        → Phê duyệt có điều kiện (APPROVED_CONDITIONAL)
            580-669: Fair                        → Phê duyệt có điều kiện (APPROVED_CONDITIONAL)
            570-579: Borderline / Gray Zone      → Thẩm định thủ công (MANUAL_REVIEW)
            < 570  : Poor / High Risk            → Từ chối tự động (REJECTED)
        """
        if credit_score >= 740:
            return "LOW", "APPROVED"
        elif credit_score >= 670:
            return "MEDIUM_LOW", "APPROVED_CONDITIONAL"
        elif credit_score >= 580:
            return "MEDIUM_HIGH", "APPROVED_CONDITIONAL"
        # [NEW RULE]: Buffer Zone (570 - 579) - Route borderline profiles to manual underwriting
        elif credit_score >= 570:
            return "HIGH", "MANUAL_REVIEW"
        else:
            return "HIGH", "REJECTED"

    # ── WoE CONTRIBUTION (EXPLAINABILITY) ───────────────────────────────────

    def _calculate_contributions(self, X_woe_row: pd.Series) -> dict:
        """Tính đóng góp điểm của từng biến theo công thức WoE Contribution.

        Công thức: Points_i = Round(WoE_i × score_factor / 10)
        """
        score_factor = self.scorecard_cfg.get("score_factor", 28.85)
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

    # ── RISK-BASED PRICING ENGINE ────────────────────────────────────────────

    def _calculate_risk_based_pricing(
        self,
        record: dict,
        risk_tier: str,
        decision: str,
    ) -> dict:
        """Tính toán gói lãi suất cá nhân hóa và hạn mức tín dụng động.

        Thuật toán:
            APR = Base Rate + Δr_risk + Δr_capital + Δr_intent
            Max Credit Limit = min(Annual Income × LTI Multiple, Hard Cap)
            Monthly PMT = P × [r(1+r)^n / ((1+r)^n - 1)]

        Chuẩn tuân thủ:
            - ECOA/Fair Lending: Không dùng gender, marital_status, person_age
            - Điều 468 BLDS Việt Nam: APR ≤ 20%/năm (chốt chặn pháp lý)
            - SPEC-ML-PRICING-2026-V1.0

        Args:
            record:    Dict thông tin hồ sơ khách hàng gốc (raw input).
            risk_tier: Phân tầng rủi ro từ mô hình ML ('LOW'/'MEDIUM_LOW'/...).
            decision:  Phán quyết tín dụng ('APPROVED'/'REJECTED'/...).

        Returns:
            dict pricing_recommendation với đầy đủ các cấu phần lãi suất,
            hạn mức tín dụng, trạng thái hạn mức và mô phỏng trả góp.
        """
        cfg = self.pricing_cfg

        # ── 1. Tính APR Cá nhân hóa ─────────────────────────────────────────
        base_rate = float(cfg.get("base_rate", 6.5))

        # Biên độ bù rủi ro (Δr_risk) theo Risk Tier
        risk_spreads = cfg.get("risk_spreads", {})
        risk_spread = float(risk_spreads.get(risk_tier, 9.0))

        # Chiết khấu sở hữu nhà (Δr_capital)
        home_ownership = str(record.get("person_home_ownership", "RENT")).upper()
        home_discounts = cfg.get("home_ownership_discounts", {})
        capital_discount = float(home_discounts.get(home_ownership, 0.0))

        # Hiệu chỉnh mục đích vay (Δr_intent)
        loan_intent = str(record.get("loan_intent", "PERSONAL")).upper()
        intent_adjustments = cfg.get("intent_adjustments", {})
        intent_adjustment = float(intent_adjustments.get(loan_intent, 0.0))

        # Tổng APR thô
        raw_apr = base_rate + risk_spread + capital_discount + intent_adjustment

        # Chốt chặn pháp lý (Statutory Cap — Điều 468 BLDS)
        min_rate = float(cfg.get("min_rate", 6.0))
        max_rate = float(cfg.get("max_rate", 24.0))
        recommended_rate = round(max(min(raw_apr, max_rate), min_rate), 2)

        # ── 2. Tính Hạn mức Tín dụng Tối đa (Dynamic Credit Limit) ──────────
        annual_income = float(record.get("person_income", 0.0))
        loan_amnt     = float(record.get("loan_amnt", 0.0))

        # Hạn mức = 0 nếu bị từ chối hoàn toàn
        if decision == "REJECTED":
            max_credit_limit = 0.0
            limit_status = "REJECTED"
        elif decision == "MANUAL_REVIEW":
            # [GRAY ZONE]: Hạn mức tạm tính / thăm dò tối đa $3,000 cho hồ sơ chờ thẩm định viên
            lti_caps  = cfg.get("max_lti_caps", {})
            hard_caps = cfg.get("max_amount_caps", {})

            lti_multiple = float(lti_caps.get(risk_tier, 0.08))
            hard_cap     = min(float(hard_caps.get(risk_tier, 5000.0)), 3000.0)  # Thăm dò tối đa $3,000

            income_based_limit = annual_income * lti_multiple
            max_credit_limit   = round(min(income_based_limit, hard_cap), 2)
            limit_status       = "MANUAL_REVIEW"
        else:
            lti_caps  = cfg.get("max_lti_caps", {})
            hard_caps = cfg.get("max_amount_caps", {})

            lti_multiple = float(lti_caps.get(risk_tier, 0.08))
            hard_cap     = float(hard_caps.get(risk_tier, 5000.0))

            income_based_limit = annual_income * lti_multiple
            max_credit_limit   = round(min(income_based_limit, hard_cap), 2)
            max_credit_limit   = max(max_credit_limit, 1000.0)  # Sàn tối thiểu $1,000

            # Đánh giá trạng thái so sánh giữa yêu cầu vay và hạn mức
            if loan_amnt <= max_credit_limit:
                limit_status = "WITHIN_LIMIT"
            else:
                limit_status = "EXCEEDS_RECOMMENDED_LIMIT"

        # ── 3. Mô phỏng Lịch Trả nợ (Amortization PMT Simulator) ─────────────
        # Số tiền giải ngân thực tế = min(loan_amnt, max_credit_limit)
        effective_principal = (
            min(loan_amnt, max_credit_limit)
            if max_credit_limit > 0
            else loan_amnt
        )

        loan_term_months = int(cfg.get("default_loan_term_months", 36))
        monthly_rate     = recommended_rate / (12 * 100)

        if monthly_rate > 0 and effective_principal > 0:
            pmt_numerator   = monthly_rate * ((1 + monthly_rate) ** loan_term_months)
            pmt_denominator = ((1 + monthly_rate) ** loan_term_months) - 1
            monthly_payment = round(effective_principal * pmt_numerator / pmt_denominator, 2)
        else:
            monthly_payment = round(effective_principal / max(loan_term_months, 1), 2)

        total_payment  = round(monthly_payment * loan_term_months, 2)
        total_interest = round(total_payment - effective_principal, 2)

        return {
            # Lãi suất & Cấu phần Waterfall
            "recommended_interest_rate": recommended_rate,
            "base_rate":                 base_rate,
            "risk_spread":               risk_spread,
            "capital_discount":          capital_discount,
            "intent_adjustment":         intent_adjustment,
            # Hạn mức tín dụng
            "max_credit_limit":          max_credit_limit,
            "requested_amount":          loan_amnt,
            "limit_status":              limit_status,
            # Mô phỏng trả góp
            "loan_term_months":          loan_term_months,
            "monthly_payment_estimate":  monthly_payment,
            "total_interest_estimate":   total_interest,
        }

    # ── SCORING ─────────────────────────────────────────────────────────────

    def score_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Chấm điểm tín dụng và tính định giá lãi suất cho một batch khách hàng."""
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
        for idx, pd_val in enumerate(y_prob):
            credit_score = self._pd_to_credit_score(pd_val)
            risk_tier, decision = self._assign_risk_tier(credit_score)

            # Tính định giá lãi suất cho từng bản ghi
            record = df.iloc[idx].to_dict()
            pricing = self._calculate_risk_based_pricing(record, risk_tier, decision)

            results.append({
                "pd_score":          round(float(pd_val), 4),
                "credit_score":      credit_score,
                "risk_tier":         risk_tier,
                "decision":          decision,
                "recommended_rate":  pricing["recommended_interest_rate"],
                "max_credit_limit":  pricing["max_credit_limit"],
                "limit_status":      pricing["limit_status"],
                "monthly_payment":   pricing["monthly_payment_estimate"],
            })

        result_df = pd.DataFrame(results)
        logger.info("Scoring complete.")
        return pd.concat([df.reset_index(drop=True), result_df], axis=1)

    def score_single(self, record: dict) -> dict:
        """Chấm điểm tín dụng và tính định giá lãi suất cho một hồ sơ khách hàng đơn lẻ.

        Returns:
            dict gồm:
            - pd_score            : Xác suất nợ xấu (0.0 – 1.0)
            - credit_score        : Điểm tín dụng FICO (300 – 850)
            - risk_tier           : Phân hạng rủi ro (LOW / MEDIUM_LOW / MEDIUM_HIGH / HIGH)
            - decision            : Quyết định tín dụng
            - contributions       : Điểm đóng góp của từng biến (WoE Contribution)
            - top_factors         : Top yếu tố tích cực / tiêu cực
            - pricing_recommendation : Gói lãi suất cá nhân hóa & hạn mức tín dụng động
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

        # Chuyển PD → Credit Score → Risk Tier & Decision
        credit_score = self._pd_to_credit_score(pd_val)
        risk_tier, decision = self._assign_risk_tier(credit_score)

        # Tính WoE Contribution cho từng biến (Explainability)
        contributions = self._calculate_contributions(X_enc.iloc[0])
        top_factors   = self._get_top_factors(contributions, top_n=3)

        # Tính định giá lãi suất cá nhân hóa (Risk-Based Pricing Engine)
        pricing_recommendation = self._calculate_risk_based_pricing(
            record=record,
            risk_tier=risk_tier,
            decision=decision,
        )

        return {
            "pd_score":               round(pd_val, 4),
            "credit_score":           credit_score,
            "risk_tier":              risk_tier,
            "decision":               decision,
            "contributions":          contributions,
            "top_factors":            top_factors,
            "pricing_recommendation": pricing_recommendation,
        }
