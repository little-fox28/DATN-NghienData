"""
Xuất 2 file CSV cho Tableau từ dữ liệu dự đoán tín dụng.

File đầu ra:
    1. data/output/model_metrics.csv   — Chỉ số mô hình (AUC, Recall, F1...) từ training_metrics.json
    2. data/output/predictions.csv     — Dự đoán per-record (pd_score, predicted_class, actual, is_test)

Cách chạy (từ PROJECT ROOT):
    python -m services.ml_engine.src.machine_learning.export_predictions
    python -m services.ml_engine.src.machine_learning.export_predictions --task credit_risk
"""

import json
import logging
import argparse
import pickle
import joblib
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional
from sklearn.model_selection import train_test_split

from services.ml_engine.src.machine_learning.config import get_task_config, get_abs_path

logger = logging.getLogger(__name__)



# HELPER — dùng chung cho cả 2 chức năng (DRY)


def load_metrics_json(
    task_name: str = "credit_risk",
    override_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Nạp training_metrics.json từ đường dẫn được ưu tiên theo thứ tự:
      1. override_path  — nếu được truyền tường minh
      2. config[metrics_output_abs]  — lấy từ task config
      3. Fallback cứng: services/ml_engine/reports/training_metrics.json

    Raises:
        FileNotFoundError: Nếu file không tồn tại ở bất kỳ đường dẫn nào.
    """
    if override_path:
        src = Path(override_path)
    else:
        config = get_task_config(task_name)
        # metrics_output_abs được config.py resolve sẵn thành đường dẫn tuyệt đối
        metrics_key = config.get(
            "metrics_output_abs",
            get_abs_path("services/ml_engine/reports/training_metrics.json"),
        )
        src = Path(str(metrics_key))

    if not src.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file metrics: {src}\n"
            "Hãy chạy pipeline training trước hoặc truyền đúng --input."
        )

    with open(src, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    logger.debug(f"  [load_metrics_json] Nạp từ: {src}")
    return data



# CHỨC NĂNG 1: Xuất model_metrics.csv từ training_metrics.json


def export_model_metrics(
    task_name: str = "credit_risk",
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    _preloaded_raw: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Đọc training_metrics.json và xuất ra model_metrics.csv cho Tableau.

    Args:
        task_name:      Tên task trong config.yaml (mặc định: credit_risk).
        input_path:     Override đường dẫn file metrics JSON (tuỳ chọn).
        output_path:    Override đường dẫn file CSV đầu ra (tuỳ chọn).
        _preloaded_raw: Dict metrics đã load sẵn — dùng khi gọi từ __main__
                        để tránh đọc file lần 2 (nội bộ, không dùng trực tiếp).

    Returns:
        DataFrame với cột: metric | class | value | is_test
        is_test = 1 → chỉ số được tính trên tập TEST (không phải train)
    """
    dest = Path(output_path) if output_path else get_abs_path("data/output/model_metrics.csv")

    logger.info("=" * 60)
    logger.info(f"XUẤT model_metrics.csv  [task={task_name}]")
    logger.info("=" * 60)

    # ── Nạp metrics JSON: dùng dict truyền vào nếu có, tránh đọc file lại ──
    raw = _preloaded_raw if _preloaded_raw is not None else load_metrics_json(task_name=task_name, override_path=input_path)

    report = raw.get("classification_report", {})

    # Tự động tìm class keys từ JSON (không hardcode "0", "1")
    SUMMARY_KEYS    = {"accuracy", "macro avg", "weighted avg"}
    class_keys      = sorted([k for k in report if k not in SUMMARY_KEYS and isinstance(report[k], dict)])
    CLASS_LABEL_MAP = {"0": "non_default", "1": "default"}

    macro_m    = report.get("macro avg",    {})
    weighted_m = report.get("weighted avg", {})

    rows: List[Dict[str, Any]] = []

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

    logger.info(f"  Đích   : {dest}")
    logger.info(f"  Số dòng: {len(df)}")
    logger.info("\n" + df.to_string(index=False))
    return df



# CHỨC NĂNG 2: Xuất predictions.csv (per-record)


def export_predictions(
    task_name: str = "credit_risk",
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    _preloaded_raw: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Chạy WoE transform + XGBoost, xuất predictions.csv per-record cho Tableau.

    Args:
        task_name:      Tên task trong config.yaml (mặc định: credit_risk).
        input_path:     Override đường dẫn file CSV đầu vào (tuỳ chọn).
        output_path:    Override đường dẫn file CSV đầu ra (tuỳ chọn).
        _preloaded_raw: Dict metrics đã load sẵn — dùng khi gọi từ __main__
                        để tránh đọc file lần 2 (nội bộ, không dùng trực tiếp).

    Returns:
        DataFrame với cột: <id_column> | features | pd_score | predicted_class | actual | is_test
        is_test: 0 = train, 1 = test (tái tạo split random_state từ config)
    """
    config = get_task_config(task_name)
    src    = Path(input_path)  if input_path  else get_abs_path("data/output/df_output.csv")
    dest   = Path(output_path) if output_path else get_abs_path("data/output/predictions.csv")

    logger.info("=" * 60)
    logger.info(f"XUẤT predictions.csv  [task={task_name}]")
    logger.info("=" * 60)

    # ── Lấy danh sách features động từ config.yaml ──
    categorical_cols: List[str] = config.get("categorical_cols", [])
    numerical_cols:   List[str] = config.get("numerical_cols",   [])
    features:         List[str] = categorical_cols + numerical_cols
    id_column:        str       = config.get("id_column", "client_ID")
    logger.info(f"  Features ({len(features)}): {features}")
    logger.info(f"  ID column  : {id_column}")

    # ── Kiểm tra an toàn artifacts trước khi load ──
    encoder_path = Path(str(config["encoder_artifact_abs"]))
    model_path   = Path(str(config["model_artifact_abs"]))

    if not encoder_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy WoE encoder: {encoder_path}\n"
            "Hãy chạy pipeline training trước."
        )
    if not model_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy model artifact: {model_path}\n"
            "Hãy chạy pipeline training trước."
        )

    with open(encoder_path, "rb") as f:
        woe_binner = pickle.load(f)
    model = joblib.load(model_path)
    logger.info(f"  WoE binner : {type(woe_binner).__name__}")
    logger.info(f"  Model      : {type(model).__name__}")

    # ── Kiểm tra an toàn file đầu vào ──
    if not src.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu đầu vào: {src}\n"
            "Hãy chạy bước export data pipeline trước."
        )

    df = pd.read_csv(src)
    logger.info(f"  Input      : {src}  ({len(df):,} hồ sơ)")

    missing_cols = [c for c in features if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Thiếu features trong dữ liệu đầu vào: {missing_cols}")

    # ── Gán is_test — dùng helper chung để đọc metrics JSON ──
    random_state: int = config.get("random_state", 42)
    target_col:   str = config.get("target_column", "loan_status")

    try:
        # Dùng dict truyền vào nếu có (đã load từ __main__), tránh đọc file lần 2
        _raw   = _preloaded_raw if _preloaded_raw is not None else load_metrics_json(task_name=task_name)
        n_test = int(_raw.get("classification_report", {}).get("macro avg", {}).get("support", 0))
        logger.info(f"  n_test (từ training_metrics.json): {n_test:,} hồ sơ")
    except FileNotFoundError:
        n_test = int(len(df) * config.get("test_size", 0.2))
        logger.warning(f"Không tìm thấy training_metrics.json — dùng test_size fallback: {n_test}")

    stratify = df[target_col] if target_col in df.columns else None
    _, idx_test = train_test_split(
        df.index, test_size=n_test, random_state=random_state, stratify=stratify
    )
    df["is_test"] = 0
    df.loc[idx_test, "is_test"] = 1
    logger.info(f"  Train: {(df['is_test']==0).sum():,}  |  Test: {(df['is_test']==1).sum():,}")

    # ── WoE transform + predict ──
    X     = df[features].copy()
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

    # ── Chọn cột đầu ra ──
    out_cols: List[str] = [id_column] + features + ["pd_score", "predicted_class"]
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



# ENTRY POINT — chạy cả 2 chức năng


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Xuất model_metrics.csv và predictions.csv cho Tableau."
    )
    parser.add_argument(
        "--task",
        default="credit_risk",
        help="Tên task trong config.yaml (mặc định: credit_risk)",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Override đường dẫn file dữ liệu đầu vào (df_output.csv)",
    )
    parser.add_argument(
        "--output-metrics",
        default=None,
        dest="output_metrics",
        help="Override đường dẫn file model_metrics.csv đầu ra",
    )
    parser.add_argument(
        "--output-predictions",
        default=None,
        dest="output_predictions",
        help="Override đường dẫn file predictions.csv đầu ra",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"EXPORT PIPELINE — 2 FILE CHO TABLEAU  [task={args.task}]")
    logger.info("=" * 60)

    # Load training_metrics.json 1 lần duy nhất, truyền vào cả 2 hàm
    try:
        shared_raw: Optional[Dict[str, Any]] = load_metrics_json(task_name=args.task)
    except FileNotFoundError as exc:
        logger.warning(str(exc))
        shared_raw = None

    export_model_metrics(
        task_name=args.task,
        output_path=args.output_metrics,
        _preloaded_raw=shared_raw,
    )

    export_predictions(
        task_name=args.task,
        input_path=args.input,
        output_path=args.output_predictions,
        _preloaded_raw=shared_raw,
    )

    logger.info("=" * 60)
    logger.info("HOÀN TẤT — 2 file đã xuất:")
    logger.info("  1. data/output/model_metrics.csv")
    logger.info("  2. data/output/predictions.csv")
    logger.info("=" * 60)
