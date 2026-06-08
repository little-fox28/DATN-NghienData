from dotenv import load_dotenv


from src.etl.pipeline import ELTPipeline
from src.utils.logger import get_logger

# Load environment variables from .env file
load_dotenv()

# Config logger
logger = get_logger(__name__)


def main() -> None:
    """
    Main entry point for running the ELT pipeline standalone.

    Creates a pipeline instance and executes it with appropriate logging.
    """
    pipeline = ELTPipeline()
    success = pipeline.run()

    if success:
        logger.info("Pipeline execution completed with status: SUCCESS ✅")
    else:
        logger.error("Pipeline execution completed with status: FAILED ❌")


if __name__ == "__main__":
    main()
