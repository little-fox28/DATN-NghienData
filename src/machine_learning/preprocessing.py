"""
preprocessing.py — Tầng 1: Tiền xử lý dữ liệu (Data Preprocessing).
Đọc dữ liệu thô, xử lý missing values, loại bỏ outlier và chia tập train/test.
"""
import logging
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

from src.machine_learning.config import (
    RAW_DATA_PATH, PROCESSED_DATA_PATH,
    TARGET_COL, FILLNA_COLS, DROP_COLS,
    TEST_SIZE, RANDOM_STATE
)

logger = logging.getLogger(__name__)


def load_raw_data() -> pd.DataFrame:
    """Đọc tệp CSV dữ liệu thô."""
    path = RAW_DATA_PATH
    if not path.exists():
        # Fallback if filename has URL encoding or spaces
        fallback = path.parent / "Credit Risk Data.csv"
        if fallback.exists():
            path = fallback
    logger.info(f"Loading raw data from: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df):,} records with {df.shape[1]} columns.")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Điền giá trị khuyết bằng Median cho các cột được cấu hình trong config.yaml."""
    logger.info("Handling missing values...")
    for col in FILLNA_COLS:
        if col in df.columns:
            median_val = df[col].median()
            n_missing = df[col].isnull().sum()
            df[col] = df[col].fillna(median_val)
            logger.info(f"  Filled {n_missing} missing values in '{col}' with median={median_val:.4f}")
    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Loại bỏ các outlier cực đoan theo quy tắc kinh doanh."""
    logger.info("Removing extreme outliers...")
    n_before = len(df)

    if "person_age" in df.columns:
        df = df[(df["person_age"] >= 18) & (df["person_age"] <= 85)]
    if "person_emp_length" in df.columns and "person_age" in df.columns:
        df = df[df["person_emp_length"] <= df["person_age"] - 18]

    n_removed = n_before - len(df)
    logger.info(f"Removed {n_removed} outlier records. Remaining: {len(df):,}")
    return df


def clean(save: bool = True) -> pd.DataFrame:
    """
    Chạy quy trình Preprocessing: Load -> Handle Missing -> Remove Outliers -> Save.
    """
    df = load_raw_data()
    df = handle_missing_values(df)
    df = remove_outliers(df)

    if save:
        Path(PROCESSED_DATA_PATH).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(PROCESSED_DATA_PATH, index=False)
        logger.info(f"Cleaned data saved to: {PROCESSED_DATA_PATH}")

    return df


def split_data(df: pd.DataFrame):
    """Chia DataFrame thành tập Train và Test."""
    logger.info(f"Splitting data: test_size={TEST_SIZE}, random_state={RANDOM_STATE}")

    cols_to_drop = [c for c in DROP_COLS if c in df.columns]
    X = df.drop(columns=cols_to_drop + [TARGET_COL], errors="ignore")
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    logger.info(f"Train size: {len(X_train):,} | Test size: {len(X_test):,}")
    logger.info(f"Default rate - Train: {y_train.mean():.2%} | Test: {y_test.mean():.2%}")

    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    df_clean = clean(save=True)
    print(f"\nPreprocessing complete. Shape: {df_clean.shape}")
