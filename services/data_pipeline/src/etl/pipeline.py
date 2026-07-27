import os
from pathlib import Path
import pandas as pd
from typing import Optional
from .extract.fetch_data import download_kaggle_file
from .extract.monitor_data import CreditDataValidator
from .transform.convert_xls_to_csv import convert_xls_to_csv
from shared.utils.logger import get_logger
from shared.utils.connector import SQLServerConnector
from .load import DataLoader

logger = get_logger(__name__)


class ETLPipeline:
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

    def __init__(self, raw_data_dir: str = RAW_DATA_DIR, processed_data_dir: str = PROCESSED_DATA_DIR, skip_db: bool = False) -> None:
        """
        Initialize the ETL pipeline.

        Args:
            raw_data_dir (str): Directory for storing raw data.
            processed_data_dir (str): Directory for storing processed/clean data.
            skip_db (bool): Whether to skip database integration.
        """
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        self.skip_db = skip_db

        self.sql_connector = None
        self.database_engine = None

        if not self.skip_db:
            # Database connection parameters
            self.server = os.getenv("DB_SERVER")
            self.database = os.getenv("DB_NAME")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASS")
            if not self.server or not self.database or not self.user or not self.password:
                logger.error("Missing database credentials in .env. Pipeline initialization aborted.")
                raise ValueError("Strict SQL Server Authentication requires DB_SERVER, DB_NAME, DB_USER, and DB_PASS.")

            # Initialize SQL Server connector and engine
            self.sql_connector = SQLServerConnector(
                server=self.server, 
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.database_engine = self.sql_connector.get_engine()

        self.raw_data_path: Optional[Path] = None
        self.transformed_data_path: Optional[Path] = Path("data/output") / "df_output.csv"

    def extract(self) -> bool:
        """
        Execute the Extract phase.
        Downloads the dataset and scans for quality issues.
        """
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline - Extract Phase")
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
                df_raw = pd.read_csv(file_to_scan)
            else:
                df_raw = pd.read_excel(file_to_scan, engine='xlrd' if file_to_scan.suffix.lower() == '.xls' else None)

            if df_raw.empty:
                logger.error("Extracted raw data is empty.")
                return None

            # Generate Data Quality Scan Report on the in-memory dataframe
            logger.info("Generating Data Quality Scan Report...")
            validator = CreditDataValidator()
            validator.report_issues(df_raw)

            logger.info("Extract phase completed successfully. Data passed to RAM.")
            return df_raw

        except Exception as e:
            logger.error(f"Unexpected error during extract phase: {e}", exc_info=True)
            return False

    def transform(self, df_raw: pd.DataFrame) -> bool:
        """
        Execute the Transform phase.
        Receives raw data directly from RAM to avoid redundant disk I/O.
        Validates, segregates into clean/quarantine, and saves the output.
        """
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline - Transform Phase")
        logger.info("=" * 60)

        if df_raw is None or df_raw.empty:
            logger.error("Transform phase failed - no raw data provided in memory.")
            return False

        try:
            logger.info("Executing Data Quality Validation and Segregation...")
            validator = CreditDataValidator()
            
            # Run Data Quality checks and split data ONCE
            df_clean, _ = validator.segregate_and_save(df_raw, output_dir=self.processed_data_dir)

            self.transformed_data_path = Path("data/output") / "df_output.csv"
            logger.info(f"Transform phase successful. Clean data saved at: {self.transformed_data_path}")
            return True

        except Exception as e:
            logger.error(f"Unexpected error during transform phase: {e}", exc_info=True)
            return False

    def load(self) -> bool:
        """
        Execute the Load phase.
        Pushes the clean dataset to the SQL Server database (Staging)
        and triggers the Stored Procedure to distribute data into Fact & Dim tables.
        """
        logger.info("=" * 60)
        logger.info("Starting ETL Pipeline - Load Phase")
        logger.info("=" * 60)

        # Check if the clean file was generated in the Transform phase
        if not self.transformed_data_path or not self.transformed_data_path.exists():
            logger.error("Load phase failed - no clean data found. Did Transform phase complete?")
            return False
        
        # Initialize DataLoader and inject the connection Engine
        loader = DataLoader(engine=self.database_engine)
        
        # Trigger the automated process: Load to Staging and distribute to Star Schema
        success = loader.load_to_staging_and_transform(
            csv_file_path=self.transformed_data_path, 
            staging_table='stg_loan',
            sp_name='sp_load_star_schema'
        )
        
        return success

    def run(self) -> bool:
        """
        Execute the complete ELT pipeline.
        Skips Load phase if no database configuration is provided.
        """
        logger.info("INITIATING ELT PIPELINE")

        # PHASE 1: EXTRACT (Load data directly to RAM)
        df_raw = self.extract()
        
        # Stop pipeline if df_raw is empty or an error occurred (returns False/None)
        if df_raw is None or isinstance(df_raw, bool):
            logger.error("Pipeline aborted at Extract Phase.")
            return False

        # PHASE 2: TRANSFORM (Pass df_raw here to avoid reading the file twice)
        if not self.transform(df_raw):
            logger.error("Pipeline aborted at Transform Phase.")
            return False
            
        # PHASE 3: LOAD (Push clean data to SQL Server & build Star Schema)
        if not self.skip_db:
            if not self.load():
                logger.error("Pipeline aborted at Load Phase.")
                return False
        else:
            logger.info("Skipping Load Phase as requested (--skip-db).")

        logger.info("=" * 60)
        logger.info("ELT PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        return True
