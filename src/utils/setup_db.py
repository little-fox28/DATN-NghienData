import os
import re
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.utils.logger import get_logger

# Load environment variables
load_dotenv()
logger = get_logger(__name__)

def build_connection_string(server: str, database: str, user: str, password: str) -> str:
    """
    Builds the SQL Server connection string enforcing SQL Server Authentication.
    Windows Authentication fallback has been completely removed for security reasons.
    """
    if not user or not password:
        logger.error("Database credentials missing. Strict SQL Server Authentication required.")
        raise ValueError("Missing DB_USER or DB_PASS in environment variables.")

    return urllib.parse.quote_plus(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={user};'
        f'PWD={password};'
        f'TrustServerCertificate=yes;'
    )

def setup_infrastructure() -> bool:
    """
    Initializes the database and executes schema files (00 -> 06).
    Returns True if successful, False if an error occurs.
    """
    # 1. READ CONFIGURATION FROM .ENV
    server = os.getenv("DB_SERVER")
    target_db = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")

    if not server or not target_db or not db_user or not db_pass:
        logger.error("Initialization aborted: Missing DB_SERVER, DB_NAME, DB_USER, or DB_PASS in .env file!")
        return False

    logger.info("=" * 60)
    logger.info("PHASE 1: AUTOMATED DB & SCHEMA INFRASTRUCTURE INITIALIZATION")
    logger.info("=" * 60)

    # 2. CONNECT TO 'MASTER' DATABASE TO CREATE TARGET DATABASE
    # isolation_level="AUTOCOMMIT" is required to run CREATE DATABASE outside a transaction block
    master_params = build_connection_string(server, 'master', db_user, db_pass)
    master_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={master_params}", isolation_level="AUTOCOMMIT")

    try:
        with master_engine.connect() as conn:
            # Check for idempotency: Ensure DB exists before creating
            db_exists = conn.execute(
                text("SELECT 1 FROM sys.databases WHERE name = :db_name"), 
                {"db_name": target_db}
            ).scalar()
            
            if not db_exists:
                logger.info(f"Database '{target_db}' does not exist. Initializing creation...")
                conn.execute(text(f"CREATE DATABASE {target_db}"))
                logger.info(f"Successfully created database: '{target_db}'")
            else:
                logger.info(f"Database '{target_db}' already exists. Skipping creation step.")
    except Exception as e:
        logger.error(f"Failed to initialize system database: {e}")
        return False

    # 3. SCAN DIRECTORIES AND EXECUTE SQL FILES SEQUENTIALLY
    target_params = build_connection_string(server, target_db, db_user, db_pass)
    target_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={target_params}")
    
    # Resolve absolute path to project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    
    schema_folder = None
    logger.info(f"Scanning for SQL schema directory starting from: {project_root}")

    # Radar scan for the specific schema directory
    for root_dir, dirs, files in os.walk(project_root):
        if "00_stg_loan.sql" in files:
            schema_folder = root_dir
            break

    if not schema_folder:
        logger.error("CRITICAL ERROR: Could not locate '00_stg_loan.sql' in the project directory!")
        return False

    logger.info(f"Target directory located: {schema_folder}")

    try:
        # Collect and sort .sql files (00 -> 06)
        sql_files = sorted([f for f in os.listdir(schema_folder) if f.endswith('.sql')])
        
        if not sql_files:
            logger.warning(f"Directory '{schema_folder}' is empty. No .sql files found for initialization.")
            return False

        logger.info(f"Found {len(sql_files)} schema files. Commencing sequential execution...")

        # Connect to the newly configured target database
        with target_engine.connect() as conn:
            for file_name in sql_files:
                file_path = os.path.join(schema_folder, file_name)
                logger.info(f"Executing script: {file_name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()

                # SAFE GO SPLITTER (Regex): Matches 'GO' only when it is on its own line (case-insensitive)
                # This prevents breaking SQL syntax if a column is named 'DimGovernment' or inside a '-- GO TO' comment.
                statements = re.split(r'(?i)^\s*GO\s*$', sql_script, flags=re.MULTILINE)
                
                for statement in statements:
                    if statement.strip():  # Skip empty or whitespace-only blocks
                        conn.execute(text(statement))
            
            # Commit all structural changes and Stored Procedures
            conn.commit()
            logger.info("=" * 60)
            logger.info("Schema tables and Stored Procedures successfully built!")
            logger.info("Infrastructure is ready. You may now trigger main.py for data ingestion.")
            logger.info("=" * 60)
            return True
            
    except Exception as e:
        logger.error(f"Fatal error while executing Schema scripts: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    setup_infrastructure()