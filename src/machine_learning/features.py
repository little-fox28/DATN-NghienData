"""
features.py — Tầng 2: Trích xuất Đặc trưng (Feature Engineering).
Dùng OrdinalEncoder cho categorical features trong pipeline chính.
"""
import pickle
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import OrdinalEncoder

from src.machine_learning.config import WOE_CAT_COLS, WOE_NUM_COLS, WOE_ARTIFACT

logger = logging.getLogger(__name__)


def build_encoder(X_train: pd.DataFrame) -> OrdinalEncoder:
    """Fit OrdinalEncoder trên tập Training cho các cột categorical."""
    logger.info("Building OrdinalEncoder for categorical features...")
    cat_cols = [c for c in WOE_CAT_COLS if c in X_train.columns]

    encoder = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=-1,
    )
    encoder.fit(X_train[cat_cols])
    logger.info(f"OrdinalEncoder fitted on {len(cat_cols)} categorical columns: {cat_cols}")
    return encoder


def save_encoder(encoder: OrdinalEncoder) -> None:
    """Lưu encoder đã fit ra file artifact (.pkl)."""
    Path(WOE_ARTIFACT).parent.mkdir(parents=True, exist_ok=True)
    with open(WOE_ARTIFACT, "wb") as f:
        pickle.dump(encoder, f)
    logger.info(f"Encoder saved to: {WOE_ARTIFACT}")


def load_encoder() -> OrdinalEncoder:
    """Tải encoder đã lưu từ artifact (.pkl)."""
    if not WOE_ARTIFACT.exists():
        raise FileNotFoundError(f"Encoder artifact not found: {WOE_ARTIFACT}. Run pipeline.py first.")
    with open(WOE_ARTIFACT, "rb") as f:
        encoder = pickle.load(f)
    logger.info(f"Encoder loaded from: {WOE_ARTIFACT}")
    return encoder


def transform(encoder: OrdinalEncoder, X: pd.DataFrame) -> pd.DataFrame:
    """Áp dụng OrdinalEncoder lên DataFrame, đảm bảo đủ các cột categorical."""
    X = X.copy()
    if hasattr(encoder, "feature_names_in_"):
        cat_cols = list(encoder.feature_names_in_)
    else:
        cat_cols = [c for c in WOE_CAT_COLS if c in X.columns]

    for col in cat_cols:
        if col not in X.columns:
            X[col] = "UNKNOWN"

    X[cat_cols] = encoder.transform(X[cat_cols])
    return X


def compute_iv_summary(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Tính Information Value (IV) cho phân tích EDA (nếu có optbinning)."""
    try:
        from optbinning import BinningProcess
    except ImportError:
        logger.warning("optbinning not available. Skipping IV computation.")
        return pd.DataFrame(columns=["Feature", "IV"])

    cat_cols = [c for c in WOE_CAT_COLS if c in X.columns]
    num_cols = [c for c in WOE_NUM_COLS if c in X.columns]
    all_cols = num_cols + cat_cols

    binner = BinningProcess(
        variable_names=all_cols,
        categorical_variables=cat_cols,
    )

    logger.info(f"Computing IV for {len(all_cols)} features...")
    binner.fit(X[all_cols], y)

    summary = binner.summary()
    iv_df = summary[["name", "iv"]].sort_values("iv", ascending=False)
    iv_df.columns = ["Feature", "IV"]
    return iv_df.reset_index(drop=True)
