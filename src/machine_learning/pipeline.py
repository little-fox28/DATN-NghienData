"""
pipeline.py — Kịch bản chạy End-to-End ML Pipeline.
Gọi tuần tự: Preprocessing -> Encoding -> Train -> Evaluate.

Sử dụng:
    python -m src.machine_learning.pipeline
    python -m src.machine_learning.pipeline --skip-preprocessing
"""
import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run(skip_preprocessing: bool = False) -> dict:
    """Chạy toàn bộ ML Pipeline."""
    logger.info("=" * 60)
    logger.info("STARTING CREDIT RISK ML PIPELINE")
    logger.info("=" * 60)

    # --- Bước 1: Preprocessing ---
    from src.machine_learning.preprocessing import clean, split_data

    if skip_preprocessing:
        import pandas as pd
        from src.machine_learning.config import PROCESSED_DATA_PATH
        logger.info(f"[SKIP] Loading existing cleaned data from: {PROCESSED_DATA_PATH}")
        df = pd.read_csv(PROCESSED_DATA_PATH)
    else:
        logger.info("[STEP 1/4] Preprocessing data...")
        df = clean(save=True)

    X_train, X_test, y_train, y_test = split_data(df)

    # --- Bước 2: Feature Encoding ---
    from src.machine_learning.features import build_encoder, save_encoder, transform

    logger.info("[STEP 2/4] Encoding categorical features (OrdinalEncoder)...")
    encoder = build_encoder(X_train)
    save_encoder(encoder)

    X_train_enc = transform(encoder, X_train)
    X_test_enc  = transform(encoder, X_test)

    # --- Bước 3: Train ---
    from src.machine_learning.train import train, save_model

    logger.info("[STEP 3/4] Training XGBoost model...")
    model = train(X_train_enc, y_train, X_test_enc, y_test)
    save_model(model)

    # --- Bước 4: Evaluate ---
    from src.machine_learning.evaluate import evaluate

    logger.info("[STEP 4/4] Evaluating model on test set...")
    metrics = evaluate(model, X_test_enc, y_test, save=True)

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info(f"  AUC-ROC : {metrics['auc']:.4f}")
    logger.info(f"  Gini    : {metrics['gini']:.4f}")
    logger.info(f"  KS Stat : {metrics['ks']:.4f}")
    logger.info("=" * 60)

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Credit Risk ML Training Pipeline")
    parser.add_argument(
        "--skip-preprocessing",
        action="store_true",
        help="Bỏ qua bước làm sạch dữ liệu, dùng lại data đã xử lý trước đó."
    )
    args = parser.parse_args()
    run(skip_preprocessing=args.skip_preprocessing)
