"""
Tầng 1: Tiền xử lý dữ liệu (Data Preprocessing).
"""
import logging
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

from services.ml_engine.src.machine_learning.config import get_abs_path

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Class xử lý dữ liệu thô, điền khuyết, loại bỏ outlier và chia tập train/test."""
    
    def __init__(self, config: dict):
        """
        Khởi tạo với cấu hình của bài toán (task config).
        """
        self.config = config
        self.raw_data_path = self.config.get("raw_data_path")
        self.target_col = self.config.get("target_column")
        # BA: Các cột này nếu NULL sẽ GIỮ NGUYÊN NaN để WoE Binner xử lý thành nhóm "Missing" riêng
        self.fillna_missing_cols = self.config.get("fillna_missing_cols", [])
        # Fallback tương thích ngược: nếu config cũ dùng fillna_median_cols thì vẫn chạy được
        self.fillna_median_cols = self.config.get("fillna_median_cols", [])
        self.drop_cols = self.config.get("drop_cols", [])
        self.test_size = self.config.get("test_size", 0.2)
        self.random_state = self.config.get("random_state", 42)
        
        # Đường dẫn lưu data đã xử lý (dung chung cho pipeline)
        self.processed_data_path = get_abs_path("data/processed/df_clean.csv")

    def load_raw_data(self) -> pd.DataFrame:
        """Đọc tệp CSV dữ liệu thô."""
        path = Path(self.raw_data_path)
        if not path.exists():
            # Fallback nếu tên file có khoảng trắng bị mã hoá thành %20
            fallback = path.parent / "Credit Risk Data.csv"
            if fallback.exists():
                path = fallback
        logger.info(f"Loading raw data from: {path}")
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df):,} records with {df.shape[1]} columns.")
        return df

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Xử lý giá trị khuyết theo chiến lược BA:
        - fillna_missing_cols: Giữ nguyên NaN → WoE Binner sẽ gom thành nhóm 'Missing' riêng (điểm baseline = 0)
        - fillna_median_cols (fallback): Điền bằng median (tương thích ngược với config cũ)
        """
        logger.info("Handling missing values...")

        # Strategy mới theo BA: chỉ log, KHÔNG điền — để NaN cho WoE Binner xử lý
        for col in self.fillna_missing_cols:
            if col in df.columns:
                n_missing = df[col].isnull().sum()
                if n_missing > 0:
                    logger.info(f"  '{col}': {n_missing} NaN values will be handled by WoE Binner as 'Missing' group")

        # Strategy cũ (fallback): điền median
        for col in self.fillna_median_cols:
            if col in df.columns:
                median_val = df[col].median()
                n_missing = df[col].isnull().sum()
                df[col] = df[col].fillna(median_val)
                logger.info(f"  [Median Fallback] Filled {n_missing} missing in '{col}' with median={median_val:.4f}")

        return df

    def remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Loại bỏ các outlier cực đoan theo quy tắc kinh doanh.
        
        Lưu ý: person_age đã bị loại khỏi feature set theo BA (không có khả năng phân biệt rủi ro
        và bị cấm theo một số quy định phòng chống phân biệt đối xử). Tuy nhiên, nếu cột này
        vẫn tồn tại trong dữ liệu gốc, vẫn dùng nó để lọc outlier TRƯỚC KHI drop.
        """
        logger.info("Removing extreme outliers...")
        n_before = len(df)

        # Lọc outlier về tuổi nếu cột vẫn còn trong dữ liệu gốc (trước bước drop)
        if "person_age" in df.columns:
            df = df[(df["person_age"] >= 18) & (df["person_age"] <= 85)]
        # Lọc thâm niên phi lý (không thể làm việc nhiều hơn tuổi - 18)
        if "person_emp_length" in df.columns and "person_age" in df.columns:
            df = df[df["person_emp_length"] <= df["person_age"] - 18]

        n_removed = n_before - len(df)
        logger.info(f"Removed {n_removed} outlier records. Remaining: {len(df):,}")
        return df

    def clean(self, save: bool = True) -> pd.DataFrame:
        """Chạy quy trình Preprocessing: Load -> Handle Missing -> Remove Outliers -> Save."""
        df = self.load_raw_data()
        df = self.handle_missing_values(df)
        df = self.remove_outliers(df)

        if save:
            self.processed_data_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.processed_data_path, index=False)
            logger.info(f"Cleaned data saved to: {self.processed_data_path}")

        return df

    def split_data(self, df: pd.DataFrame):
        """Chia DataFrame thành tập Train và Test."""
        logger.info(f"Splitting data: test_size={self.test_size}, random_state={self.random_state}")

        cols_to_drop = [c for c in self.drop_cols if c in df.columns]
        X = df.drop(columns=cols_to_drop + [self.target_col], errors="ignore")
        y = df[self.target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, stratify=y
        )

        logger.info(f"Train size: {len(X_train):,} | Test size: {len(X_test):,}")
        logger.info(f"Target rate - Train: {y_train.mean():.2%} | Test: {y_test.mean():.2%}")

        return X_train, X_test, y_train, y_test