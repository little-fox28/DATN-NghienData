"""
train.py — Tầng 3: Huấn luyện Mô hình (Model Training).
Huấn luyện mô hình XGBoost Classifier và lưu artifact.
"""
import joblib
import logging
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier

from src.machine_learning.config import MODEL_PARAMS, MODEL_ARTIFACT, RANDOM_STATE

logger = logging.getLogger(__name__)


def build_model() -> XGBClassifier:
    """Khởi tạo mô hình XGBoost từ tham số trong config.yaml."""
    params = {k: v for k, v in MODEL_PARAMS.items()}
    params["seed"] = params.pop("random_state", RANDOM_STATE)
    return XGBClassifier(**params)


def train(X_train: pd.DataFrame, y_train: pd.Series,
          X_val: pd.DataFrame = None, y_val: pd.Series = None) -> XGBClassifier:
    """Huấn luyện mô hình XGBoost."""
    model = build_model()
    logger.info(f"Training XGBoost model with {X_train.shape[1]} features on {len(X_train):,} records...")

    eval_set = [(X_val, y_val)] if X_val is not None else None
    model.fit(
        X_train, y_train,
        eval_set=eval_set,
        verbose=False,
    )

    logger.info("Model training completed successfully.")
    return model


def save_model(model: XGBClassifier) -> None:
    """Lưu mô hình đã huấn luyện ra file artifact (.joblib)."""
    Path(MODEL_ARTIFACT).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_ARTIFACT)
    logger.info(f"Model saved to: {MODEL_ARTIFACT}")


def load_model() -> XGBClassifier:
    """Tải mô hình đã được lưu từ artifact (.joblib)."""
    if not MODEL_ARTIFACT.exists():
        raise FileNotFoundError(f"Model artifact not found: {MODEL_ARTIFACT}. Run pipeline.py first.")
    model = joblib.load(MODEL_ARTIFACT)
    logger.info(f"Model loaded from: {MODEL_ARTIFACT}")
    return model
