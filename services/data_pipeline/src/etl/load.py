import re
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from shared.utils.logger import get_logger

logger = get_logger(__name__)

class DataLoader:
    def __init__(self, engine):
        """
        Initialize with the connection engine provided by the Pipeline.
        Note: Database credentials and selection are strictly handled by the injected engine.
        """
        self.engine = engine

    def _is_valid_identifier(self, identifier: str) -> bool:
        """
        SECURITY FIX: Validates SQL identifiers (table names, SP names) to prevent SQL Injection.
        Ensures that the input contains only alphanumeric characters and underscores.
        """
        return bool(re.match(r'^[a-zA-Z0-9_]+$', identifier))

    def load_csv(self, csv_file_path: Path) -> pd.DataFrame:
        """
        Reads clean data from CSV file.
        """
        logger.info(f"Reading cleaned data from file: {csv_file_path}...")
        df_clean = pd.read_csv(csv_file_path)
        return df_clean

    def truncate_table(self, conn, staging_table: str = 'stg_loan') -> None:
        """
        Truncates the staging table.
        """
        # SECURITY CHECK: Prevent SQL Injection
        if not self._is_valid_identifier(staging_table):
            raise ValueError(f"Security risk detected: Invalid staging table name: '{staging_table}'")
            
        logger.info(f"Truncating staging table: {staging_table}...")
        conn.execute(text(f"TRUNCATE TABLE {staging_table}"))

    def bulk_insert(self, conn, df_clean: pd.DataFrame, staging_table: str = 'stg_loan') -> None:
        """
        Performs bulk insert into the staging table.
        """
        # SECURITY CHECK: Prevent SQL Injection
        if not self._is_valid_identifier(staging_table):
            raise ValueError(f"Security risk detected: Invalid staging table name: '{staging_table}'")

        logger.info(f"Starting bulk insert of {len(df_clean)} rows into '{staging_table}'...")
        df_clean.to_sql(
            name=staging_table,
            con=conn,
            if_exists='append',   # MUST be 'append' to preserve the pre-built schema
            index=False,
            chunksize=10000       # PERFORMANCE FIX: Increased from 1000 to 10000 for fast_executemany optimization
        )
        logger.info(f"Successfully loaded data into '{staging_table}'.")

    def run_stored_procedure(self, conn, sp_name: str = 'sp_load_star_schema') -> None:
        """
        Executes the star schema stored procedure.
        """
        # SECURITY CHECK: Prevent SQL Injection
        if not self._is_valid_identifier(sp_name):
            raise ValueError(f"Security risk detected: Invalid procedure name: '{sp_name}'")

        logger.info(f"Triggering Star Schema transformation: EXEC {sp_name}...")
        conn.execute(text(f"EXEC {sp_name}"))
        logger.info("Data distribution to Fact and Dimension tables completed successfully!")

    # def load_to_staging_and_transform(self, csv_file_path: Path, staging_table: str = 'stg_loan', sp_name: str = 'sp_load_star_schema') -> bool:
    #     """
    #     Executes Phase 2.2 (Load to Staging) and Phase 2.3 (In-Database Transform) sequentially.
    #     """
    #     return bool(re.match(r'^[a-zA-Z0-9_]+$', identifier)

    def load_to_staging_and_transform(self, csv_file_path: Path, staging_table: str = 'stg_loan', sp_name: str = 'sp_load_star_schema') -> bool:
        """
        Executes Phase 2.2 (Load to Staging) and Phase 2.3 (In-Database Transform) sequentially.
        """
        # SECURITY CHECK: Prevent SQL Injection for dynamic DDL/EXEC commands
        if not self._is_valid_identifier(staging_table) or not self._is_valid_identifier(sp_name):
            logger.error(f"Security risk detected: Invalid table ('{staging_table}') or procedure name ('{sp_name}'). Aborting load process.")
            return False

        try:
            logger.info(f"Reading cleaned data from file: {csv_file_path}...")
            df_clean = pd.read_csv(csv_file_path)

            if df_clean.empty:
                logger.warning("CSV file is empty. No data to load!")
                return False

            # Use engine.begin() for automatic Transaction management (Rollback on failure)
            with self.engine.begin() as conn:
                
                # Step 1: Clean the staging table (TRUNCATE is faster and cleaner than DELETE)
                logger.info(f"Truncating staging table: {staging_table}...")
                conn.execute(text(f"TRUNCATE TABLE {staging_table}"))

                # Step 2: Bulk insert new data into staging table
                logger.info(f"Starting bulk insert of {len(df_clean)} rows into '{staging_table}'...")
                df_clean.to_sql(
                    name=staging_table,
                    con=conn,
                    if_exists='append',   # MUST be 'append' to preserve the pre-built schema
                    index=False,
                    chunksize=10000       # PERFORMANCE FIX: Increased from 1000 to 10000 for fast_executemany optimization
                )
                logger.info(f"Successfully loaded data into '{staging_table}'.")

                # Step 3: Execute the Stored Procedure to distribute data into Star Schema
                logger.info(f"Triggering Star Schema transformation: EXEC {sp_name}...")
                conn.execute(text(f"EXEC {sp_name}"))
                logger.info("Data distribution to Fact and Dimension tables completed successfully!")

            return True

        except Exception as e:
            logger.error(f"Critical error during data load process: {e}", exc_info=True)
            return False