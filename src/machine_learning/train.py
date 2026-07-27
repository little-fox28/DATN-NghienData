"""
Tầng 3: Huấn luyện Mô hình (Model Training).
"""
import joblib
import logging
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Class đảm nhiệm việc huấn luyện và lưu trữ mô hình Machine Learning."""
    
    def __init__(self, config: dict):
        """
        Khởi tạo với cấu hình bài toán.
        """
        self.config = config
        self.model_params = self.config.get("params", {})
        self.model_artifact = self.config.get("model_artifact_abs")
        self.random_state = self.config.get("random_state", 42)
        
        self.model = None

    def build_model(self) -> XGBClassifier:
        """Khởi tạo mô hình XGBoost từ tham số trong config."""
        params = {k: v for k, v in self.model_params.items()}
        # XGBoost dùng tham số 'seed' cho tính ngẫu nhiên
        params["seed"] = params.pop("random_state", self.random_state)
        
        self.model = XGBClassifier(**params)
        return self.model

    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: pd.DataFrame = None, y_val: pd.Series = None) -> XGBClassifier:
        """Huấn luyện mô hình XGBoost."""
        if self.model is None:
            self.build_model()
            
        logger.info(f"Training XGBoost model with {X_train.shape[1]} features on {len(X_train):,} records...")

        eval_set = [(X_val, y_val)] if X_val is not None and y_val is not None else None
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False,
        )

        logger.info("Model training completed successfully.")
        return self.model

    def save_model(self) -> None:
        """Lưu mô hình đã huấn luyện ra file artifact (.joblib)."""
        if self.model is None:
            raise ValueError("Model is not trained yet. Run train() first.")
            
        path_obj = Path(self.model_artifact)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path_obj)
        logger.info(f"Model saved to: {self.model_artifact}")

    def load_model(self) -> XGBClassifier:
        """Tải mô hình đã được lưu từ artifact (.joblib)."""
        path_obj = Path(self.model_artifact)
        if not path_obj.exists():
            raise FileNotFoundError(f"Model artifact not found: {self.model_artifact}. Run pipeline.py first.")
            
        self.model = joblib.load(path_obj)
        logger.info(f"Model loaded from: {self.model_artifact}")
        return self.model

