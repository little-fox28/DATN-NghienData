"""
Tầng 2: Trích xuất Đặc trưng (Feature Engineering).
"""
import pickle
import logging
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import OrdinalEncoder

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Class đảm nhiệm việc mã hóa biến phân loại và kỹ nghệ đặc trưng."""
    
    def __init__(self, config: dict):
        """
        Khởi tạo với cấu hình bài toán.
        """
        self.config = config
        self.cat_cols = self.config.get("categorical_cols", [])
        self.encoder_artifact = self.config.get("encoder_artifact_abs")
        
        self.encoder = None

    def build_encoder(self, X_train: pd.DataFrame) -> OrdinalEncoder:
        """Fit OrdinalEncoder trên tập Training cho các cột categorical."""
        logger.info("Building OrdinalEncoder for categorical features...")
        
        # Chỉ chọn những cột categorical có trong X_train
        valid_cat_cols = [c for c in self.cat_cols if c in X_train.columns]
        
        self.encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1,
        )
        self.encoder.fit(X_train[valid_cat_cols])
        
        logger.info(f"OrdinalEncoder fitted on {len(valid_cat_cols)} categorical columns: {valid_cat_cols}")
        return self.encoder

    def save_encoder(self) -> None:
        """Lưu encoder đã fit ra file artifact (.pkl)."""
        if self.encoder is None:
            raise ValueError("Encoder is not built yet. Run build_encoder() first.")
            
        path_obj = Path(self.encoder_artifact)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(path_obj, "wb") as f:
            pickle.dump(self.encoder, f)
        logger.info(f"Encoder saved to: {self.encoder_artifact}")

    def load_encoder(self) -> OrdinalEncoder:
        """Tải encoder đã lưu từ artifact (.pkl)."""
        path_obj = Path(self.encoder_artifact)
        if not path_obj.exists():
            raise FileNotFoundError(f"Encoder artifact not found: {self.encoder_artifact}. Run pipeline.py first.")
            
        with open(path_obj, "rb") as f:
            self.encoder = pickle.load(f)
        logger.info(f"Encoder loaded from: {self.encoder_artifact}")
        return self.encoder

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Áp dụng OrdinalEncoder lên DataFrame, đảm bảo đủ các cột categorical."""
        if self.encoder is None:
            raise ValueError("Encoder is not built or loaded. Run load_encoder() first.")
            
        X = X.copy()
        
        if hasattr(self.encoder, "feature_names_in_"):
            valid_cat_cols = list(self.encoder.feature_names_in_)
        else:
            valid_cat_cols = [c for c in self.cat_cols if c in X.columns]

        for col in valid_cat_cols:
            if col not in X.columns:
                X[col] = "UNKNOWN"

        X[valid_cat_cols] = self.encoder.transform(X[valid_cat_cols])
        return X