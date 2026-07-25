"""
config.py — Loader cấu hình cho module Machine Learning.
Đọc các tham số từ config.yaml. Không hardcode giá trị trong code.
"""
import yaml
from pathlib import Path

# Thư mục gốc dự án (DATN/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Đường dẫn đến file cấu hình ML
CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config() -> dict:
    """Đọc và trả về toàn bộ cấu hình từ config.yaml."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def get_abs_path(relative_path: str) -> Path:
    """Chuyển đổi đường dẫn tương đối sang đường dẫn tuyệt đối."""
    return ROOT_DIR / relative_path


# Load cấu hình
cfg = load_config()

# Đường dẫn dữ liệu
RAW_DATA_PATH       = get_abs_path(cfg["data"]["raw_path"])
PROCESSED_DATA_PATH = get_abs_path(cfg["data"]["processed_path"])
FINAL_DATA_PATH     = get_abs_path(cfg["data"]["final_path"])

# Tham số tiền xử lý
TARGET_COL       = cfg["preprocessing"]["target_column"]
ID_COL           = cfg["preprocessing"]["id_column"]
FILLNA_COLS      = cfg["preprocessing"]["fillna_median_cols"]
DROP_COLS        = cfg["preprocessing"]["drop_cols"]
TEST_SIZE        = cfg["preprocessing"]["test_size"]
RANDOM_STATE     = cfg["preprocessing"]["random_state"]

# Tham số trích xuất đặc trưng
WOE_CAT_COLS     = cfg["features"]["woe_categorical_cols"]
WOE_NUM_COLS     = cfg["features"]["woe_numerical_cols"]
WOE_ARTIFACT     = get_abs_path(cfg["features"]["woe_artifact_path"])

# Tham số mô hình
MODEL_TYPE       = cfg["model"]["type"]
MODEL_PARAMS     = cfg["model"]["params"]
MODEL_ARTIFACT   = get_abs_path(cfg["model"]["artifact_path"])

# Tham số đánh giá
METRICS_PATH     = get_abs_path(cfg["evaluation"]["metrics_output_path"])
FIGURES_DIR      = get_abs_path(cfg["evaluation"]["figures_output_dir"])

# Tham số Scorecard
SCORECARD_CFG    = cfg["scorecard"]
