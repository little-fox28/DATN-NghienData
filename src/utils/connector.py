import urllib.parse
from sqlalchemy import create_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SQLServerConnector:
    def __init__(self, server, database, user=None, password=None):
        self.server = server
        self.database = database
        self.user = user
        self.password = password
        # Khởi tạo engine ngay khi tạo đối tượng
        self.engine = self._create_engine()

    def _create_engine(self):
        """Hàm nội bộ tạo kết nối SQL Server bằng Windows Authentication"""
        if self.user and self.password:
            logger.info("Đang cấu hình kết nối bằng [SQL Server Authentication]...")
            params = urllib.parse.quote_plus(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.server};'
                f'DATABASE={self.database};'
                f'UID={self.user};'
                f'PWD={self.password};'
                f'TrustServerCertificate=yes;'
        )
            
        else:
            logger.info("Đang cấu hình kết nối bằng [Windows Authentication]...")
            params = urllib.parse.quote_plus(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.server};'
                f'DATABASE={self.database};'
                f'Trusted_Connection=yes;'
                f'TrustServerCertificate=yes;'
            )
        return create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)


    def get_engine(self):
        return self.engine