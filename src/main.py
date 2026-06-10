from dotenv import load_dotenv

from src.etl.pipeline import ELTPipeline
from src.utils.logger import get_logger
import os
from src.utils.setup_db import setup_infrastructure
# Load environment variables from .env file
load_dotenv()

# Config logger
logger = get_logger(__name__)


def main() -> None:
    """
    Main entry point for running the ETL pipeline standalone.

    Creates a pipeline instance and executes it with appropriate logging.
    """
    try:
        setup_infrastructure() 
        # 1. Lấy thông tin Server và Database một cách bảo mật từ file .env
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_NAME")



        # Kiểm tra an toàn: Nếu biến môi trường trống thì báo lỗi và dừng chương trình
        if not server or not database:
            logger.error("Thiếu thông tin DB_SERVER hoặc DB_NAME trong file .env!")
            return

        logger.info(f"Đã nhận cấu hình đích: Server='{server}', Database='{database}'")

        # 2. Khởi tạo cỗ máy Pipeline và truyền thông số Database vào
        
        pipeline = ELTPipeline(server=server, database=database)
        success = pipeline.run()

        if success:
            logger.info("Pipeline execution completed with status: SUCCESS ✅")
        else:
            logger.error("Pipeline execution completed with status: FAILED ❌")

    except Exception as e:
        logger.error(f"Đã xảy ra lỗi hệ thống nghiêm trọng: {e}", exc_info=True)
    
if __name__ == "__main__":
    main()