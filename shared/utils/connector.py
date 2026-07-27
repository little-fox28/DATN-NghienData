import urllib.parse
from sqlalchemy import create_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SQLServerConnector:
    def __init__(self, server, database, user, password):
        """
        Initialize the SQL Server Connector with strict SQL Server Authentication.
        """
        self.server = server
        self.database = database
        self.user = user
        self.password = password
        
        # Enforce SQL Server Authentication credentials
        if not self.user or not self.password:
            logger.error("Database initialization failed: SQL Server Authentication requires both username and password.")
            raise ValueError("Database credentials missing. Windows Authentication fallback is disabled.")
            
        # Initialize engine immediately upon object creation
        self.engine = self._create_engine()

    def _create_engine(self):
        """
        Internal method to create a SQL Server connection engine using strict SQL Server Authentication.
        """
        logger.info("Configuring database connection using strict [SQL Server Authentication]...")
        
        params = urllib.parse.quote_plus(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.user};'
            f'PWD={self.password};'
            f'TrustServerCertificate=yes;'
        )
            
        return create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)


    def get_engine(self):
        return self.engine