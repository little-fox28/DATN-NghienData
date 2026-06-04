import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataLoader:
    def __init__(self, database_engine, database_name: str):
        """
        Nhận động cơ kết nối và tên Database từ Pipeline truyền sang.
        """
        self.engine = database_engine
        self.database_name = database_name

    def push_to_sql(self, csv_file_path: Path, table_name: str = 'stg_loan') -> bool:
        """
        Thực thi việc đẩy dữ liệu từ file CSV lên SQL Server.
        """
        try:
            logger.info(f"Reading clean data from {csv_file_path}...")
            df_clean = pd.read_csv(csv_file_path)
            
            logger.info(f"Pushing {len(df_clean)} rows to table '{table_name}' in Database '{self.database_name}'...")

            # Đẩy dữ liệu lên Database
            df_clean.to_sql(
                name=table_name,      
                con=self.engine,           
                if_exists='replace',  
                index=False,          
                chunksize=1000        
            )

            logger.info(f"Load phase successful. All clean data loaded to '{table_name}'.")
            return True

        except Exception as e:
            logger.error(f"Unexpected error during load phase: {e}", exc_info=True)
            return False