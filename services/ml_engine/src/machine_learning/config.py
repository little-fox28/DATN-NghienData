import yaml
from pathlib import Path
# Thư mục gốc dự án (DATN/)
ROOT_DIR = Path(__file__).resolve().parents[4]
# Đường dẫn đến file cấu hình ML
CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
def load_raw_config() -> dict:
    """Đọc toàn bộ file yaml thô."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
def get_abs_path(relative_path: str) -> Path:
    """Chuyển đổi đường dẫn tương đối sang tuyệt đối."""
    return ROOT_DIR / relative_path

# --- Load cấu hình tổng ---
_raw_cfg = load_raw_config()
GLOBAL_CFG = _raw_cfg.get("global", {})
def get_task_config(task_name: str = "credit_risk") -> dict:
    """
    Trích xuất cấu hình cho một Bài toán cụ thể từ config.yaml.
    
    Args:
        task_name: Tên bài toán ('credit_risk', 'loan_intent', 'interest_rate_pricing', ...)
        
    Returns:
        Dictionary chứa toàn bộ cấu hình của task đó.
    """
    tasks = _raw_cfg.get("tasks", {})
    if task_name not in tasks:
        raise KeyError(f"Task '{task_name}' không tồn tại trong config.yaml. Các task hợp lệ: {list(tasks.keys())}")
    
    task_cfg = tasks[task_name]
    
    # Tự động chuyển đổi các đường dẫn tương đối thành tuyệt đối
    task_cfg["raw_data_path"] = get_abs_path(GLOBAL_CFG.get("raw_data_path", "data/raw/Credit%20Risk%20Data.csv"))
    task_cfg["model_artifact_abs"] = get_abs_path(task_cfg["model_artifact"])
    task_cfg["encoder_artifact_abs"] = get_abs_path(task_cfg["encoder_artifact"])
    task_cfg["metrics_output_abs"] = get_abs_path(task_cfg["metrics_output"])
    task_cfg["figures_dir_abs"] = get_abs_path(task_cfg["figures_dir"])
    
    return task_cfg
    
# --- Cấu hình tương thích mặc định cho Bài toán 1 (Credit Risk) ---
DEFAULT_TASK_CFG = get_task_config("credit_risk")
RAW_DATA_PATH       = DEFAULT_TASK_CFG["raw_data_path"]
TARGET_COL          = DEFAULT_TASK_CFG["target_column"]
ID_COL              = DEFAULT_TASK_CFG["id_column"]
FILLNA_COLS         = DEFAULT_TASK_CFG["fillna_median_cols"]
DROP_COLS           = DEFAULT_TASK_CFG["drop_cols"]
TEST_SIZE           = DEFAULT_TASK_CFG["test_size"]
RANDOM_STATE        = DEFAULT_TASK_CFG["random_state"]
WOE_CAT_COLS        = DEFAULT_TASK_CFG["categorical_cols"]
WOE_NUM_COLS        = DEFAULT_TASK_CFG["numerical_cols"]
WOE_ARTIFACT        = DEFAULT_TASK_CFG["encoder_artifact_abs"]
MODEL_PARAMS        = DEFAULT_TASK_CFG["params"]
MODEL_ARTIFACT      = DEFAULT_TASK_CFG["model_artifact_abs"]
METRICS_PATH        = DEFAULT_TASK_CFG["metrics_output_abs"]
FIGURES_DIR         = DEFAULT_TASK_CFG["figures_dir_abs"]
SCORECARD_CFG       = DEFAULT_TASK_CFG["scorecard"]

PROCESSED_DATA_PATH = get_abs_path("data/processed/df_clean.csv")
