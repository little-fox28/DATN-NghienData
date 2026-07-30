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
    Kết nối các tầng Preprocessing -> Feature Engineering -> Training -> Evaluation.
    """

    def __init__(self, task_name: str = "credit_risk", skip_preprocessing: bool = False):
        self.task_name = task_name
        self.skip_preprocessing = skip_preprocessing
        
        # Load cấu hình cụ thể cho bài toán
        self.config = get_task_config(self.task_name)
        # Bổ sung task_name vào config để các lớp bên dưới sử dụng (vd: đặt tên biểu đồ)
        self.config["task_name"] = self.task_name
        
        # Import các Class OOP vừa xây dựng
        from services.ml_engine.src.machine_learning.preprocessing import DataPreprocessor
        from services.ml_engine.src.machine_learning.features import FeatureEngineer
        from services.ml_engine.src.machine_learning.train import ModelTrainer
        from services.ml_engine.src.machine_learning.evaluate import ModelEvaluator
        
        # Khởi tạo các module con với cùng một config duy nhất
        self.preprocessor = DataPreprocessor(self.config)
        self.feature_eng = FeatureEngineer(self.config)
        self.trainer = ModelTrainer(self.config)
        self.evaluator = ModelEvaluator(self.config)

    def run(self) -> Optional[dict]:
        """Thực thi toàn bộ pipeline tuần tự."""
        logger.info("=" * 60)
        logger.info(f"STARTING ML PIPELINE FOR TASK: {self.task_name.upper()}")
        logger.info("=" * 60)

        try:
            # --- Bước 1: Preprocessing ---
            logger.info("[STEP 1/4] Preprocessing data...")
            if self.skip_preprocessing:
                import pandas as pd
                logger.info(f"[SKIP] Loading existing cleaned data from: {self.preprocessor.processed_data_path}")
                df = pd.read_csv(self.preprocessor.processed_data_path)
            else:
                df = self.preprocessor.clean(save=True)
            
            X_train, X_test, y_train, y_test = self.preprocessor.split_data(df)

            # --- Bước 2: Feature Engineering (WoE Binning) ---
            logger.info("[STEP 2/4] WoE Binning & encoding features...")
            # WoE là supervised encoding — cần y_train để tính WoE value theo tỷ lệ Default/Non-default
            self.feature_eng.build_encoder(X_train, y_train)
            self.feature_eng.save_encoder()
            
            X_train_enc = self.feature_eng.transform(X_train)
            X_test_enc = self.feature_eng.transform(X_test)

            # --- Bước 3: Training ---
            logger.info(f"[STEP 3/4] Training model for task: {self.task_name}...")
            self.trainer.train(X_train_enc, y_train, X_test_enc, y_test)
            self.trainer.save_model()

            # --- Bước 4: Evaluation ---
            logger.info("[STEP 4/4] Evaluating model...")
            metrics = self.evaluator.evaluate(
                model=self.trainer.model, 
                X_test=X_test_enc, 
                y_test=y_test, 
                save=True
            )
            
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
    
    args = parser.parse_args()
    
    pipeline = MLPipeline(task_name=args.task, skip_preprocessing=args.skip_preprocessing)
    pipeline.run()

