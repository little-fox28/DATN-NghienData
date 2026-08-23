"""
Tầng 3: Huấn luyện Mô hình (Model Training).
"""
from typing import Optional, Union, Any
import joblib
import logging
import pandas as pd
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV

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
        params = self.model_params.copy()
        # XGBoost dùng tham số 'seed' cho tính ngẫu nhiên
        params["seed"] = params.pop("random_state", self.random_state)
        
        self.model = XGBClassifier(**params)
        return self.model

    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None, y_val: Optional[pd.Series] = None) -> CalibratedClassifierCV:
        """Huấn luyện mô hình XGBoost và hiệu chuẩn xác suất (Probability Calibration)."""
        if self.model is None:
            self.build_model()
            
        logger.info(f"Training base XGBoost model with {X_train.shape[1]} features on {len(X_train):,} records...")

        # 1. Huấn luyện mô hình XGBoost cơ sở
        eval_set = [(X_val, y_val)] if X_val is not None and y_val is not None else None
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False,
        )
        logger.info("Base XGBoost model trained successfully.")

        # 2. Hiệu chuẩn xác suất bằng CalibratedClassifierCV (Platt Scaling / sigmoid)
        logger.info("Applying probability calibration via CalibratedClassifierCV (method='sigmoid')...")
        try:
            from sklearn.frozen import FrozenEstimator
            calibrated_model = CalibratedClassifierCV(
                estimator=FrozenEstimator(self.model),
                method="sigmoid"
            )
        except ImportError:
            # Tương thích ngược với các phiên bản scikit-learn cũ hơn (< 1.4)
            calibrated_model = CalibratedClassifierCV(
                estimator=self.model,
                method="sigmoid",
                cv="prefit"
            )

        # Fit calibrator trên tập validation (nếu có) hoặc tập train
        if X_val is not None and y_val is not None:
            calibrated_model.fit(X_val, y_val)
        else:
            calibrated_model.fit(X_train, y_train)

        self.model = calibrated_model
        logger.info("Probability calibration completed successfully.")
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

