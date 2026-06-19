from dotenv import load_dotenv

from src.etl.pipeline import ETLPipeline
from src.utils.logger import get_logger
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
    import argparse
    parser = argparse.ArgumentParser(description="Run ETL Pipeline")
    parser.add_argument("--skip-db", action="store_true", help="Skip database setup and load phases")
    args = parser.parse_args()

    try:
        if not args.skip_db:
            # 1. INITIALIZE INFRASTRUCTURE (DB, Tables, Stored Procedures)
            logger.info("Verifying and setting up database infrastructure...")
            is_setup_success = setup_infrastructure() 
            
            # Abort immediately if DB setup fails
            if not is_setup_success:
                logger.error("Pipeline execution aborted due to infrastructure setup failure.")
                return

            logger.info("Infrastructure is fully operational. Initializing ETL Pipeline...")
        else:
            logger.info("Skipping database infrastructure setup. Initializing ETL Pipeline (Dry Run)...")

        # 2. INITIALIZE AND RUN PIPELINE
        pipeline = ETLPipeline(skip_db=args.skip_db)
        success = pipeline.run()

        if success:
            logger.info("Pipeline execution completed with status: SUCCESS ✅")
        else:
            logger.error("Pipeline execution completed with status: FAILED ❌")

    except Exception as e:
        logger.error(f"Critical system error: {e}", exc_info=True)


if __name__ == "__main__":
    main()