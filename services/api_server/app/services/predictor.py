"""
Predictor Service — Business logic cho ML scoring.
Tách biệt khỏi router để dễ test và mở rộng.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.ml_engine.src.machine_learning.config import get_task_config
from services.ml_engine.src.machine_learning.predict import ModelPredictor


def _load_default_predictor() -> ModelPredictor | None:
    """Khởi tạo ModelPredictor cho credit_risk khi API start. Auto-train nếu chưa có model."""
    try:
        config = get_task_config("credit_risk")
        config["task_name"] = "credit_risk"

        model_file = Path(config["model_artifact_abs"])
        encoder_file = Path(config["encoder_artifact_abs"])

        if not model_file.exists() or not encoder_file.exists():
            print("⚡ Model artifacts not found. Triggering pipeline training...")
            from services.ml_engine.src.machine_learning.pipeline import MLPipeline
            MLPipeline(task_name="credit_risk", skip_preprocessing=True).run()

        return ModelPredictor(config)
    except Exception as err:
        print(f"⚠️ Không thể khởi tạo default predictor: {err}")
        return None


def score_application(record: dict, task: str = "credit_risk") -> dict:
    """
    Chạy ML scoring cho một hồ sơ vay với cấu hình cập nhật từ config.yaml.

    Args:
        record: dict chứa thông tin hồ sơ (từ LoanApplication.model_dump())
        task:   tên task, mặc định "credit_risk"

    Returns:
        dict kết quả scoring từ ModelPredictor.score_single()
    """
    task_cfg = get_task_config(task)
    task_cfg["task_name"] = task
    predictor = ModelPredictor(task_cfg)
    return predictor.score_single(record)
