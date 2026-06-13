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
        # 1. INITIALIZE INFRASTRUCTURE (DB, Tables, Stored Procedures)
        logger.info("Verifying and setting up database infrastructure...")
        is_setup_success = setup_infrastructure() 
        
        # SECURITY & LOGIC CHECK: Abort immediately if DB setup fails
        if not is_setup_success:
            logger.error("Pipeline execution aborted due to infrastructure setup failure. ")
            return

        logger.info("Infrastructure is fully operational. Initializing ELT Pipeline...")

        # 2. INITIALIZE AND RUN PIPELINE
        # Note: ELTPipeline now handles strict SQL Server Auth automatically inside its constructor.
        pipeline = ELTPipeline()
        success = pipeline.run()

        if success:
            logger.info("Pipeline execution completed with status: SUCCESS ✅")
        else:
            logger.error("Pipeline execution completed with status: FAILED ❌")

    except Exception as e:
        logger.error(f"Đã xảy ra lỗi hệ thống nghiêm trọng: {e}", exc_info=True)
    
if __name__ == "__main__":
    main()