"""
Script độc lập: Tự động tạo bảng (nếu chưa có) và nạp predictions.csv vào SQL Server.

Cách chạy (từ PROJECT ROOT):
    python -m services.data_pipeline.src.etl.load_ml_predictions

Luồng:
    1. Kiểm tra stg_predictions / FactMLPrediction / sp_load_ml_predictions đã tồn tại chưa
    2. Nếu chưa → tự chạy 07_stg_predictions.sql, 08_FactMLPrediction.sql, 09_sp_load_ml_predictions.sql
    3. predictions.csv → stg_predictions → sp_load_ml_predictions → FactMLPrediction
"""

import os
import re
import sys
import logging
from pathlib import Path

from sqlalchemy import text
from services.data_pipeline.src.etl.pipeline import ETLPipeline

logger = logging.getLogger(__name__)

# services/data_pipeline/src/etl/load_ml_predictions.py → 5 cấp lên là ROOT
ROOT_DIR        = Path(__file__).resolve().parent.parent.parent.parent.parent
SQL_DIR         = Path(__file__).resolve().parent.parent / "sql_model"
PREDICTIONS_CSV = ROOT_DIR / "data" / "output" / "predictions.csv"

SETUP_FILES = [
    SQL_DIR / "07_stg_predictions.sql",
    SQL_DIR / "08_FactMLPrediction.sql",
    SQL_DIR / "09_sp_load_ml_predictions.sql",
]

# ── SQL constants — định nghĩa tập trung, dễ đổi tên nếu cần ────────────────────
STAGING_TABLE = "stg_predictions"
SP_NAME       = "sp_load_ml_predictions"
FACT_TABLE    = "dbo.FactMLPrediction"




def _run_sql_file(engine, sql_path: Path) -> None:
    """Đọc file SQL, tách theo GO và thực thi từng batch."""
    sql_text = sql_path.read_text(encoding="utf-8")

    # Tách các batch theo GO (kể cả GO với comment sau)
    batches = re.split(r"^\s*GO\s*(?:--[^\n]*)?\s*$", sql_text, flags=re.MULTILINE | re.IGNORECASE)
    batches = [b.strip() for b in batches if b.strip()]

    with engine.begin() as conn:
        for batch in batches:
            conn.execute(text(batch))

    logger.info(f"   Đã chạy: {sql_path.name}")




def setup_ml_tables(engine) -> bool:
    """
    - stg_predictions        : luôn drop và recreate (staging table, phải khớp CSV mới nhất)
    - FactMLPrediction        : chỉ tạo nếu chưa có
    - sp_load_ml_predictions  : chỉ tạo nếu chưa có (CREATE OR ALTER → luôn update)
    """
    CHECK_SQL = f"""
        SELECT
            CASE WHEN OBJECT_ID('{FACT_TABLE}', 'U') IS NOT NULL THEN 1 ELSE 0 END AS fact_ok,
            CASE WHEN OBJECT_ID('{SP_NAME}',    'P') IS NOT NULL THEN 1 ELSE 0 END AS sp_ok
    """

    with engine.connect() as conn:
        row = conn.execute(text(CHECK_SQL)).fetchone()
        fact_ok, sp_ok = row

    stg_file  = SQL_DIR / "07_stg_predictions.sql"
    fact_file = SQL_DIR / "08_FactMLPrediction.sql"
    sp_file   = SQL_DIR / "09_sp_load_ml_predictions.sql"

    # Staging: luôn drop & recreate để đảm bảo schema khớp với predictions.csv
    logger.info(f"  Recreate {STAGING_TABLE} (staging table luôn được làm mới)...")
    try:
        _run_sql_file(engine, stg_file)
    except Exception as e:
        logger.error(f"  Lỗi khi tạo {STAGING_TABLE}: {e}", exc_info=True)
        return False

    # FactMLPrediction: chỉ tạo nếu chưa có
    if not fact_ok:
        logger.info(f"  Tạo {FACT_TABLE}...")
        try:
            _run_sql_file(engine, fact_file)
        except Exception as e:
            logger.error(f"  Lỗi khi tạo {FACT_TABLE}: {e}", exc_info=True)
            return False
    else:
        logger.info(f"  {FACT_TABLE} đã tồn tại — giữ nguyên")

    # Stored Procedure: CREATE OR ALTER → luôn update
    logger.info(f"  Cập nhật {SP_NAME}...")
    try:
        _run_sql_file(engine, sp_file)
    except Exception as e:
        logger.error(f"  Lỗi khi tạo {SP_NAME}: {e}", exc_info=True)
        return False

    logger.info("  Setup hoàn tất!")
    return True





def main() -> bool:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Kiểm tra file đầu vào
    if not PREDICTIONS_CSV.exists():
        logger.error(f"Không tìm thấy: {PREDICTIONS_CSV}")
        logger.error("Hãy chạy trước: python -m services.ml_engine.src.machine_learning.export_predictions")
        return False

    logger.info("=" * 60)
    logger.info("LOAD ML PREDICTIONS → SQL SERVER")
    logger.info("=" * 60)
    logger.info(f"  Nguồn: {PREDICTIONS_CSV}")

    # Khởi tạo pipeline — tái dùng toàn bộ logic kết nối từ ETLPipeline.__init__
    # (đọc DB_SERVER, DB_NAME, DB_USER, DB_PASS từ .env)
    pipeline = ETLPipeline()
    engine   = pipeline.database_engine

    # Tự động tạo bảng nếu chưa có
    logger.info("=" * 60)
    logger.info("BƯỚC 1: KIỂM TRA / TẠO BẢNG")
    logger.info("=" * 60)
    if not setup_ml_tables(engine):
        return False

    # Load: CSV → stg_predictions → FactMLPrediction
    logger.info("=" * 60)
    logger.info("BƯỚC 2: NẠP DỮ LIỆU")
    logger.info("=" * 60)
    success = pipeline.load_predictions()

    if success:
        logger.info("=" * 60)
        logger.info("HOÀN TẤT — FactMLPrediction đã được cập nhật")
        logger.info("=" * 60)
    else:
        logger.error("Load thất bại — kiểm tra log phía trên")

    return success


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
