"""
predict.py — Tầng 5: Dự đoán (Inference).
Tải mô hình và encoder đã lưu, thực hiện chấm điểm tín dụng.
"""
import math
import logging
import numpy as np
import pandas as pd

from src.machine_learning.config import SCORECARD_CFG
from src.machine_learning.train import load_model
from src.machine_learning.features import load_encoder, transform

logger = logging.getLogger(__name__)


def _pd_to_credit_score(pd_value: float) -> int:
    """Chuyển đổi Xác suất Nợ xấu (PD) sang Điểm Tín dụng (300 - 850)."""
    target_score = SCORECARD_CFG["target_score"]
    target_odds  = SCORECARD_CFG["target_odds"]
    pdo          = SCORECARD_CFG["pdo"]

    pd_value = max(min(pd_value, 0.9999), 0.0001)
    odds  = pd_value / (1 - pd_value)
    factor = pdo / math.log(2)
    score = int(round(target_score - factor * math.log(odds / target_odds)))
    return max(min(score, 850), 300)


def _assign_risk_tier(pd_value: float) -> tuple[str, str]:
    """Phân loại khách hàng vào nhóm rủi ro và đưa ra quyết định."""
    if pd_value < 0.10:
        return "LOW", "APPROVED"
    elif pd_value < 0.25:
        return "MEDIUM", "APPROVED"
    elif pd_value < 0.40:
        return "HIGH", "MANUAL_REVIEW"
    else:
        return "CRITICAL", "REJECTED"


def score_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Chấm điểm tín dụng cho một batch khách hàng."""
    logger.info(f"Scoring {len(df):,} records...")

    encoder = load_encoder()
    model   = load_model()

    X_enc = transform(encoder, df)

    # Đảm bảo đủ tất cả các cột mà model yêu cầu
    if hasattr(model, "feature_names_in_"):
        expected_features = list(model.feature_names_in_)
        for col in expected_features:
            if col not in X_enc.columns:
                X_enc[col] = 0.0
        X_enc = X_enc[expected_features]

    y_prob = model.predict_proba(X_enc)[:, 1]

    results = []
    for pd_val in y_prob:
        credit_score = _pd_to_credit_score(pd_val)
        risk_tier, decision = _assign_risk_tier(pd_val)
        results.append({
            "pd_score":     round(float(pd_val), 4),
            "credit_score": credit_score,
            "risk_tier":    risk_tier,
            "decision":     decision,
        })

    result_df = pd.DataFrame(results)
    logger.info("Scoring complete.")
    return pd.concat([df.reset_index(drop=True), result_df], axis=1)


def score_single(record: dict) -> dict:
    """Chấm điểm tín dụng cho một hồ sơ khách hàng đơn lẻ."""
    df = pd.DataFrame([record])
    result = score_batch(df)
    return result[["pd_score", "credit_score", "risk_tier", "decision"]].iloc[0].to_dict()
