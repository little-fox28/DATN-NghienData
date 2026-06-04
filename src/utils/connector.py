import urllib.parse
from sqlalchemy import create_engine

class SQLServerConnector:
    def __init__(self, server, database):
        self.server = server
        self.database = database
        # Khởi tạo engine ngay khi tạo đối tượng
        self.engine = self._create_engine()

    def _create_engine(self):
        """Hàm nội bộ tạo kết nối SQL Server bằng Windows Authentication"""
        params = urllib.parse.quote_plus(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'Trusted_Connection=yes;'
            f'TrustServerCertificate=yes;'
        )
        return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    def get_engine(self):
        return self.engine