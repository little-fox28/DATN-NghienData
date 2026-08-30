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

    def fine_tune(self, X_new: pd.DataFrame, y_new: pd.Series) -> CalibratedClassifierCV:
        """Học tăng cường (Incremental / Warm-start) trên tập dữ liệu mới mà không cần học lại từ tập cũ."""
        path_obj = Path(self.model_artifact)
        if not path_obj.exists():
            logger.warning("Chưa có mô hình đã huấn luyện trước đó. Chuyển sang huấn luyện mới.")
            return self.train(X_new, y_new)

        logger.info(f"Loading existing model from {self.model_artifact} for incremental fine-tuning...")
        existing_calibrated = joblib.load(path_obj)
        
        # Trích xuất base XGBoost booster
        base_model = getattr(existing_calibrated, "estimator", existing_calibrated)
        base_model = getattr(base_model, "estimator", base_model)
        existing_booster = base_model.get_booster()

        # Đảm bảo đúng thứ tự và danh sách đặc trưng của booster hiện tại
        booster_features = existing_booster.feature_names
        if booster_features:
            for col in booster_features:
                if col not in X_new.columns:
                    X_new[col] = 0.0
            X_new = X_new[booster_features].astype(float)

        # Tạo XGBoost tiếp nối với tốc độ học nhỏ để tinh chỉnh
        params = self.model_params.copy()
        params["seed"] = params.pop("random_state", self.random_state)
        params["n_estimators"] = max(10, min(30, len(X_new)))
        params["learning_rate"] = 0.02

        self.model = XGBClassifier(**params)
        logger.info(f"Fine-tuning XGBoost with {len(X_new)} new manually approved records (warm-start)...")
        self.model.fit(X_new, y_new, xgb_model=existing_booster)

        # Gắn booster vừa học tăng cường vào CalibratedClassifierCV wrapper hiện tại
        try:
            from sklearn.frozen import FrozenEstimator
            existing_calibrated.estimator = FrozenEstimator(self.model)
        except Exception:
            existing_calibrated.estimator = self.model
            
        self.model = existing_calibrated
        logger.info("Incremental fine-tuning completed and model wrapper updated successfully.")
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

