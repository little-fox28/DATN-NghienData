import pandas as pd
from pathlib import Path
from sqlalchemy import text
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataLoader:
    def __init__(self, engine):
        """
        Nhận động cơ kết nối (engine) từ Pipeline truyền sang.
        Lưu ý: Không cần truyền database_name nữa vì engine đã ngầm chứa thông tin đó.
        """
        self.engine = engine

    def load_to_staging_and_transform(self, csv_file_path: Path, staging_table: str = 'stg_loan', sp_name: str = 'load_star_schema') -> bool:
        """
        Thực thi Phase 2.2 (Load to Staging) và Phase 2.3 (In-Database Transform) liên hoàn.
        """
        try:
            logger.info(f"Đang đọc dữ liệu sạch từ file: {csv_file_path}...")
            df_clean = pd.read_csv(csv_file_path)

            if df_clean.empty:
                logger.warning("File CSV không có dữ liệu để nạp!")
                return False

            # Dùng engine.begin() để mở Transaction. Lỗi giữa chừng sẽ tự động Rollback (hủy bỏ)
            with self.engine.begin() as conn:
                
                # Bước 1: Dọn sạch bảng đệm (Staging) của lần chạy trước (Thay vì dùng replace)
                logger.info(f"Dọn rác bảng đệm: TRUNCATE TABLE {staging_table}...")
                conn.execute(text(f"TRUNCATE TABLE {staging_table}"))

                # Bước 2: Nạp lô dữ liệu mới vào bảng đệm
                logger.info(f"Bắt đầu đẩy {len(df_clean)} dòng vào {staging_table}...")
                df_clean.to_sql(
                    name=staging_table,
                    con=conn,
                    if_exists='append',   # BẮT BUỘC LÀ 'append' để giữ nguyên cấu trúc bảng đã tạo
                    index=False,
                    chunksize=1000        # Chia nhỏ mỗi lần nạp 1000 dòng để không tràn RAM
                )
                logger.info(f"Đẩy dữ liệu vào {staging_table} thành công.")

                # Bước 3: Kích hoạt Stored Procedure phân bổ dữ liệu vào Star Schema
                logger.info(f"Kích hoạt SQL Server xử lý Star Schema: EXEC {sp_name}...")
                conn.execute(text(f"EXEC {sp_name}"))
                logger.info("Quá trình phân bổ dữ liệu vào Fact và Dim hoàn tất!")

            return True

        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng trong quá trình Load dữ liệu: {e}", exc_info=True)
            return False