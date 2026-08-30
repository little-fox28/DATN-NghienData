"""
Kịch bản chạy End-to-End ML Pipeline.

Sử dụng:
    python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk
    python -m services.ml_engine.src.machine_learning.pipeline --task credit_risk --skip-preprocessing
"""
import logging
import argparse
from typing import Optional

from services.ml_engine.src.machine_learning.config import get_task_config

logger = logging.getLogger(__name__)

class MLPipeline:
    """
    Quản lý quy trình Machine Learning Pipeline End-to-End.
    Hỗ trợ cả 2 chế độ:
    - Huấn luyện từ đầu (Full Re-train)
    - Học tăng cường từ phê duyệt mới (Incremental Fine-tuning / Warm-start) mà không cần học lại dữ liệu cũ.
    """

    def __init__(self, task_name: str = "credit_risk", skip_preprocessing: bool = False, incremental: bool = False):
        self.task_name = task_name
        self.skip_preprocessing = skip_preprocessing
        self.incremental = incremental
        
        # Load cấu hình cụ thể cho bài toán
        self.config = get_task_config(self.task_name)
        self.config["task_name"] = self.task_name
        
        # Import các Class OOP
        from services.ml_engine.src.machine_learning.preprocessing import DataPreprocessor
        from services.ml_engine.src.machine_learning.features import FeatureEngineer
        from services.ml_engine.src.machine_learning.train import ModelTrainer
        from services.ml_engine.src.machine_learning.evaluate import ModelEvaluator
        
        self.preprocessor = DataPreprocessor(self.config)
        self.feature_eng = FeatureEngineer(self.config)
        self.trainer = ModelTrainer(self.config)
        self.evaluator = ModelEvaluator(self.config)

    def run(self) -> Optional[dict]:
        """Thực thi toàn bộ pipeline tuần tự."""
        mode_str = "INCREMENTAL FINE-TUNING (NEW APPROVED DATA ONLY)" if self.incremental else "FULL RETRAINING"
        logger.info("=" * 60)
        logger.info(f"STARTING ML PIPELINE [{mode_str}] FOR TASK: {self.task_name.upper()}")
        logger.info("=" * 60)

        try:
            if self.incremental:
                # --- Chế độ Học Tăng Cường (Không nạp dữ liệu cũ) ---
                logger.info("[INCREMENTAL 1/4] Loading newly approved labeled records from enriched stream...")
                df_new = self.preprocessor.load_incremental_data()
                df_new_clean = self.preprocessor.handle_missing_values(df_new)
                df_new_clean = self.preprocessor.remove_outliers(df_new_clean)
                
                target_col = self.preprocessor.target_col
                drop_cols = [c for c in self.preprocessor.drop_cols if c in df_new_clean.columns]
                X_new = df_new_clean.drop(columns=[target_col] + drop_cols, errors="ignore")
                y_new = df_new_clean[target_col].astype(int)

                logger.info(f"[INCREMENTAL 2/4] Transforming {len(X_new)} new records using existing WoE Binner...")
                self.feature_eng.load_encoder()
                X_new_enc = self.feature_eng.transform(X_new)
                
                # Chỉ giữ lại đúng các cột đặc trưng số WoE mà mô hình XGBoost yêu cầu
                expected_cols = [c for c in (self.feature_eng.num_cols + self.feature_eng.cat_cols)]
                for col in expected_cols:
                    if col not in X_new_enc.columns:
                        X_new_enc[col] = 0.0
                X_new_enc = X_new_enc[expected_cols].astype(float)

                logger.info("[INCREMENTAL 3/4] Warm-starting and fine-tuning XGBoost with new approved knowledge...")
                self.trainer.fine_tune(X_new_enc, y_new)
                self.trainer.save_model()

                logger.info("[INCREMENTAL 4/4] Updating readable model trees & artifacts...")
                try:
                    from services.ml_engine.models_readable.model_reader import create_readable_models
                    create_readable_models()
                    logger.info("Readable models updated successfully.")
                except Exception as e:
                    logger.warning(f"Failed to update readable models: {e}")

                logger.info("=" * 60)
                logger.info("INCREMENTAL LEARNING COMPLETED SUCCESSFULLY! ✨")
                logger.info("=" * 60)
                return {"incremental_samples": len(X_new), "status": "success"}

            # --- Chế độ Huấn luyện Đầy đủ (Full Pipeline) ---
            # --- Bước 1: Preprocessing ---
            logger.info("[STEP 1/5] Preprocessing data...")
            if self.skip_preprocessing:
                import pandas as pd
                logger.info(f"[SKIP] Loading existing cleaned data from: {self.preprocessor.processed_data_path}")
                df = pd.read_csv(self.preprocessor.processed_data_path)
            else:
                df = self.preprocessor.clean(save=True)
            
            X_train, X_test, y_train, y_test = self.preprocessor.split_data(df)

            # --- Bước 2: Feature Engineering (WoE Binning) ---
            logger.info("[STEP 2/5] WoE Binning & encoding features...")
            self.feature_eng.build_encoder(X_train, y_train)
            self.feature_eng.save_encoder()
            
            X_train_enc = self.feature_eng.transform(X_train)
            X_test_enc = self.feature_eng.transform(X_test)

            # --- Bước 3: Training ---
            logger.info(f"[STEP 3/5] Training model for task: {self.task_name}...")
            self.trainer.train(X_train_enc, y_train, X_test_enc, y_test)
            self.trainer.save_model()

            # --- Bước 4: Evaluation ---
            logger.info("[STEP 4/5] Evaluating model...")
            metrics = self.evaluator.evaluate(
                model=self.trainer.model, 
                X_test=X_test_enc, 
                y_test=y_test, 
                save=True
            )
            # --- Bước 5: Generate Readable Models ---
            logger.info("[STEP 5/5] Generating readable JSON models...")
            try:
                from services.ml_engine.models_readable.model_reader import create_readable_models
                create_readable_models()
                logger.info("Readable models generated successfully.")
            except Exception as e:
                logger.warning(f"Failed to generate readable models: {e}")
            
            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    parser = argparse.ArgumentParser(description="Multi-task ML Training Pipeline")
    parser.add_argument("--task", type=str, default="credit_risk", help="Tên bài toán cần chạy (vd: credit_risk, loan_intent)")
    parser.add_argument("--skip-preprocessing", action="store_true", help="Bỏ qua làm sạch dữ liệu, dùng data đã xử lý")
    parser.add_argument("--incremental", action="store_true", help="Chế độ học tăng cường chỉ trên dữ liệu mới được thẩm định (không đọc tệp cũ)")
    
    args = parser.parse_args()
    
    pipeline = MLPipeline(task_name=args.task, skip_preprocessing=args.skip_preprocessing, incremental=args.incremental)
    pipeline.run()

