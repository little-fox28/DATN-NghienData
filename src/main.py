from dotenv import load_dotenv
import os
import argparse

from src.etl.pipeline import ELTPipeline
from src.utils.logger import get_logger
from src.utils.setup_db import setup_infrastructure

# Load environment variables from .env file
load_dotenv()

# Config logger
logger = get_logger(__name__)


def main() -> None:
    """
    Parses command-line arguments and executes the Credit Risk ELT pipeline.
    
    This function initializes database infrastructure if needed, handles
    configuration from environment variables, and executes the appropriate pipeline
    flow based on execution flags.
    """
    parser = argparse.ArgumentParser(description="Credit Risk ELT Pipeline")
    parser.add_argument("--skip-db", action="store_true", help="Chỉ chạy Extract và Transform, không Load vào Database")
    args = parser.parse_args()

    try:
        if args.skip_db:
            logger.info("Chế độ chạy độc lập: Bỏ qua Database Setup và Load (--skip-db).")
            pipeline = ELTPipeline(skip_db=True)
        else:
            logger.info("Chế độ chạy đầy đủ: Thiết lập và Load vào Database.")
            is_setup_success = setup_infrastructure() 
            
            # SECURITY & LOGIC CHECK: Abort immediately if DB setup fails
            if not is_setup_success:
                logger.error("Pipeline execution aborted due to infrastructure setup failure.")
                return

            logger.info("Infrastructure is fully operational. Initializing ELT Pipeline...")
            pipeline = ELTPipeline(skip_db=False)

        success = pipeline.run()

        if success:
            logger.info("Pipeline execution completed with status: SUCCESS ✅")
        else:
            logger.error("Pipeline execution completed with status: FAILED ❌")

    except Exception as e:
        logger.error(f"Đã xảy ra lỗi hệ thống nghiêm trọng: {e}", exc_info=True)

if __name__ == "__main__":
    main()