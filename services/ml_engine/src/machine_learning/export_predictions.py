"""
Xuất 2 file CSV cho Tableau từ dữ liệu dự đoán tín dụng.

File đầu ra:
    1. data/output/model_metrics.csv   — Chỉ số mô hình (AUC, Recall, F1...) từ training_metrics.json
    2. data/output/predictions.csv     — Dự đoán per-record (pd_score, predicted_class, actual, is_test)

Cách chạy (từ PROJECT ROOT):
    python -m services.ml_engine.src.machine_learning.export_predictions
"""

import json
import logging
import argparse
import pickle
import joblib
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

from services.ml_engine.src.machine_learning.config import get_task_config, get_abs_path

logger = logging.getLogger(__name__)

FEATURES = [
    "loan_grade",
    "person_home_ownership",
    "cb_person_default_on_file",
    "loan_intent",
    "loan_to_income_ratio",
    "debt_to_income_ratio",
    "person_income",
    "loan_int_rate",
    "person_emp_length",
    "loan_amnt",
]


# ══════════════════════════════════════════════════════════════
# CHỨC NĂNG 1: Xuất model_metrics.csv từ training_metrics.json
# ══════════════════════════════════════════════════════════════

def export_model_metrics(
    input_path: str | None = None,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Đọc training_metrics.json và xuất ra model_metrics.csv cho Tableau.

    Cột đầu ra: metric | class | value | is_test
    is_test = 1 → chỉ số được tính trên tập TEST (không phải train)
    """
    src  = Path(input_path)  if input_path  else get_abs_path("services/ml_engine/reports/training_metrics.json")
    dest = Path(output_path) if output_path else get_abs_path("data/output/model_metrics.csv")

    logger.info("=" * 60)
    logger.info("XUẤT model_metrics.csv")
    logger.info("=" * 60)

    if not src.exists():
        raise FileNotFoundError(f"Không tìm thấy: {src}")

    with open(src, "r", encoding="utf-8") as f:
        raw = json.load(f)

    report = raw.get("classification_report", {})

    # Tự động tìm class keys từ JSON (không hardcode "0", "1")
    SUMMARY_KEYS = {"accuracy", "macro avg", "weighted avg"}
    class_keys   = sorted([k for k in report if k not in SUMMARY_KEYS and isinstance(report[k], dict)])
    CLASS_LABEL_MAP = {"0": "non_default", "1": "default"}

    macro_m    = report.get("macro avg",    {})
    weighted_m = report.get("weighted avg", {})

    rows = []

    # Chỉ số tổng hợp model
    for key, val in [("auc", raw.get("auc", 0.0)), ("gini", raw.get("gini", 0.0)), ("ks", raw.get("ks", 0.0))]:
        rows.append({"metric": key, "class": "model", "value": round(val, 4), "is_test": 1})
    rows.append({"metric": "accuracy", "class": "model", "value": round(report.get("accuracy", 0.0), 4), "is_test": 1})

    # Metrics theo từng class — đọc động từ JSON
    for cls_key in class_keys:
        cls_data  = report[cls_key]
        cls_label = CLASS_LABEL_MAP.get(cls_key, f"class_{cls_key}")
        for metric_name in ("precision", "recall", "f1-score", "support"):
            if metric_name not in cls_data:
                continue
            raw_val = cls_data[metric_name]
            value   = int(raw_val) if metric_name == "support" else round(float(raw_val), 4)
            rows.append({"metric": metric_name.replace("-", "_"), "class": cls_label, "value": value, "is_test": 1})

    # Macro avg & Weighted avg
    for cls_label, avg_m in [("macro_avg", macro_m), ("weighted_avg", weighted_m)]:
        for metric_name in ("precision", "recall", "f1-score"):
            if metric_name in avg_m:
                rows.append({"metric": metric_name.replace("-", "_"), "class": cls_label,
                             "value": round(avg_m[metric_name], 4), "is_test": 1})

    df = pd.DataFrame(rows, columns=["metric", "class", "value", "is_test"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)

    logger.info(f"  Nguồn : {src}")
    logger.info(f"  Đích   : {dest}")
    logger.info(f"  Số dòng: {len(df)}")
    logger.info("\n" + df.to_string(index=False))
    return df


# ══════════════════════════════════════════════════════════════
# CHỨC NĂNG 2: Xuất predictions.csv (per-record)
# ══════════════════════════════════════════════════════════════

def export_predictions(
    task_name: str = "credit_risk",
    input_path: str | None = None,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Chạy WoE transform + XGBoost, xuất predictions.csv per-record cho Tableau.

    Cột đầu ra: client_ID | 10 features | pd_score | predicted_class | actual | is_test
    is_test: 0 = train, 1 = test (tái tạo split random_state từ config)
    """
    config = get_task_config(task_name)
    src    = Path(input_path)  if input_path  else get_abs_path("data/output/df_output.csv")
    dest   = Path(output_path) if output_path else get_abs_path("data/output/predictions.csv")

    logger.info("=" * 60)
    logger.info("XUẤT predictions.csv")
    logger.info("=" * 60)

    # Load artifacts
    with open(config["encoder_artifact_abs"], "rb") as f:
        woe_binner = pickle.load(f)
    model = joblib.load(config["model_artifact_abs"])
    logger.info(f"  WoE binner : {type(woe_binner).__name__}")
    logger.info(f"  Model      : {type(model).__name__}")

    # Load data
    df = pd.read_csv(src)
    logger.info(f"  Input      : {src}  ({len(df):,} hồ sơ)")

    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu features: {missing}")

    # Gán is_test — dùng số hồ sơ tuyệt đối từ training_metrics.json

    random_state = config.get("random_state", 42)
    target_col   = config.get("target_column", "loan_status")

    # Đọc n_test từ training_metrics.json (macro avg support)
    _metrics_src = get_abs_path("services/ml_engine/reports/training_metrics.json")
    if _metrics_src.exists():
        with open(_metrics_src, "r", encoding="utf-8") as _f:
            _raw = json.load(_f)
        n_test = int(_raw.get("classification_report", {}).get("macro avg", {}).get("support", 0))
    else:
        n_test = int(len(df) * config.get("test_size", 0.2))  # fallback nếu không có json
        logger.warning(f"Không tìm thấy training_metrics.json — dùng test_size fallback: {n_test}")

    logger.info(f" n_test (từ training_metrics.json): {n_test:,} hồ sơ")

    stratify = df[target_col] if target_col in df.columns else None
    _, idx_test = train_test_split(
        df.index, test_size=n_test, random_state=random_state, stratify=stratify
    )
    df["is_test"] = 0
    df.loc[idx_test, "is_test"] = 1
    logger.info(f"  Train: {(df['is_test']==0).sum():,}  |  Test: {(df['is_test']==1).sum():,}")

    # WoE transform + predict
    X     = df[FEATURES].copy()
    X_woe = woe_binner.transform(X)
    if hasattr(model, "feature_names_in_"):
        for col in model.feature_names_in_:
            if col not in X_woe.columns:
                X_woe[col] = 0.0
        X_woe = X_woe[model.feature_names_in_]

    df["pd_score"]        = model.predict_proba(X_woe)[:, 1]
    df["predicted_class"] = model.predict(X_woe)

    if target_col in df.columns:
        df["actual"] = df[target_col]

    # Chọn cột đầu ra
    out_cols = ["client_ID"] + FEATURES + ["pd_score", "predicted_class"]
    if "actual" in df.columns:
        out_cols.append("actual")
    out_cols.append("is_test")
    out_cols = [c for c in out_cols if c in df.columns]

    result = df[out_cols].copy()
    dest.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(dest, index=False)

    logger.info(f"  Đích      : {dest}")
    logger.info(f"  Số hồ sơ : {len(result):,}")
    logger.info(f"  Số cột   : {len(result.columns)}")
    logger.info(f"  Cột      : {result.columns.tolist()}")
    return result


# ══════════════════════════════════════════════════════════════
# ENTRY POINT — chạy cả 2 chức năng
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


    logger.info("=" * 60)
    logger.info("EXPORT PIPELINE — 2 FILE CHO TABLEAU")
    logger.info("=" * 60)

    export_model_metrics(
        
    )

    export_predictions(
    
    )

    logger.info("=" * 60)
    logger.info("HOÀN TẤT — 2 file đã xuất:")
    logger.info("  1. data/output/model_metrics.csv")
    logger.info("  2. data/output/predictions.csv")
    logger.info("=" * 60)
