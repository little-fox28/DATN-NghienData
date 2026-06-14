from pathlib import Path
from typing import Optional

from .extract.fetch_data import download_kaggle_file
from .extract.monitor_data import CreditDataValidator
from .transform.convert_xls_to_csv import convert_xls_to_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ELTPipeline:
    """
    Manages the Extract-Load-Transform pipeline.

    This class orchestrates the complete data processing workflow, starting
    with Kaggle dataset extraction and followed by transformation.
    """

    KAGGLE_DATASET = "alexdister/credit-risk-dataset"
    TARGET_FILE = "Credit%20Risk%20Data.csv"
    RAW_DATA_DIR = "data/raw"
    PROCESSED_DATA_DIR = "data/processed"
    TRANSFORMED_FILE = "transformed.csv"

    def __init__(self, raw_data_dir: str = RAW_DATA_DIR, processed_data_dir: str = PROCESSED_DATA_DIR) -> None:
        """
        Initialize the ELT pipeline.

        Args:
            raw_data_dir (str): Directory for storing raw data.
            processed_data_dir (str): Directory for storing processed/clean data.
        """
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        self.raw_data_path: Optional[Path] = None
        self.transformed_data_path: Optional[Path] = Path("data/output") / "df_output.csv"

    def extract(self) -> bool:
        """
        Execute the Extract phase.
        Downloads the dataset and scans for quality issues.
        """
        logger.info("=" * 60)
        logger.info("Starting ELT Pipeline - Extract Phase")
        logger.info("=" * 60)

        try:
            # 1. Download
            self.raw_data_path = download_kaggle_file(
                dataset_name=self.KAGGLE_DATASET,
                file_name=self.TARGET_FILE,
                destination_dir=self.raw_data_dir
            )

            if not self.raw_data_path:
                logger.error("Extract phase failed - file could not be obtained")
                return False

            # 2. Scan and Report
            import pandas as pd
            file_to_scan = self.raw_data_path
            if file_to_scan.is_dir():
                files = list(file_to_scan.glob("*.csv")) + list(file_to_scan.glob("*.xls"))
                if not files:
                    logger.error("No data files found for scanning.")
                    return False
                file_to_scan = files[0]

            logger.info(f"Scanning raw data: {file_to_scan}")
            if file_to_scan.suffix.lower() == '.csv':
                df = pd.read_csv(file_to_scan)
            else:
                df = pd.read_excel(file_to_scan, engine='xlrd' if file_to_scan.suffix.lower() == '.xls' else None)

            validator = CreditDataValidator()
            validator.report_issues(df)

            logger.info("Extract phase completed successfully.")
            return True

        except Exception as e:
            logger.error(f"Unexpected error during extract phase: {e}", exc_info=True)
            return False

    def transform(self) -> bool:
        """
        Execute the Transform phase.
        Converts XLS to CSV (if needed) and segregates data into clean/quarantine (Feature 2).
        """
        logger.info("=" * 60)
        logger.info("Starting ELT Pipeline - Transform Phase")
        logger.info("=" * 60)

        if not self.raw_data_path:
            logger.error("Transform phase failed - no raw data path available.")
            return False

        try:
            import pandas as pd
            
            # 1. Identify input file
            input_file = self.raw_data_path
            if input_file.is_dir():
                files = list(input_file.glob("*.csv")) + list(input_file.glob("*.xls"))
                if not files:
                    logger.error("No data files found for transformation.")
                    return False
                input_file = files[0]

            # 2. Check for bypass: If already CSV, don't call conversion
            if input_file.suffix.lower() == '.csv':
                logger.info(f"Bypassing conversion: {input_file.name} is already in CSV format.")
                working_csv = input_file
            else:
                interim_csv = Path(self.raw_data_dir) / self.TRANSFORMED_FILE
                success = convert_xls_to_csv(
                    input_path=str(input_file),
                    output_path=str(interim_csv)
                )
                if not success:
                    logger.error("Transform phase failed during XLS to CSV conversion")
                    return False
                working_csv = interim_csv

            # 3. Segregate and Save to data/processed (Feature 2)
            logger.info(f"Loading data from {working_csv} for segregation...")
            df = pd.read_csv(working_csv)
            validator = CreditDataValidator()
            df_clean, _ = validator.segregate_and_save(df, output_dir=self.processed_data_dir)

            self.transformed_data_path = Path("data/output") / "df_output.csv"
            logger.info(f"Transform phase successful. Clean data saved at: {self.transformed_data_path}")
            return True

        except Exception as e:
            logger.error(f"Unexpected error during transform phase: {e}", exc_info=True)
            return False

    def run(self) -> bool:
        """
        Execute the complete ELT pipeline.
        """
        logger.info("Initializing ELT Pipeline")

        if not self.extract():
            return False

        if not self.transform():
            return False

        logger.info("=" * 60)
        logger.info("ELT Pipeline completed successfully!")
        logger.info("=" * 60)
        return True
