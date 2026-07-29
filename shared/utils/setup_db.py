import os
import re
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from shared.utils.logger import get_logger


# Load environment variables from .env
load_dotenv()

logger = get_logger(__name__)


# Only schema files 00 -> 06 are executed inside CreditRiskDB.
# The config file is executed separately through master + AUTOCOMMIT.
SCHEMA_FILES = [
    "00_stg_loan.sql",
    "01_DimCustomer.sql",
    "02_DimLocation.sql",
    "03_DimPurpose.sql",
    "04_DimGrade.sql",
    "05_FactLoan.sql",
    "06_load_star_schema.sql",
]


def build_connection_string(
    server: str,
    database: str,
    user: str,
    password: str,
) -> str:
    """
    Build a SQL Server connection string using
    SQL Server Authentication.
    """

    if not server:
        raise ValueError(
            "Missing DB_SERVER in environment variables."
        )

    if not database:
        raise ValueError(
            "Missing database name."
        )

    if not user or not password:
        logger.error(
            "Database credentials are missing. "
            "SQL Server Authentication is required."
        )

        raise ValueError(
            "Missing DB_USER or DB_PASS "
            "in environment variables."
        )

    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

    return urllib.parse.quote_plus(
        connection_string
    )


def create_sql_engine(
    server: str,
    database: str,
    user: str,
    password: str,
    autocommit: bool = False,
) -> Engine:
    """
    Create a SQLAlchemy engine for SQL Server.
    """

    connection_params = build_connection_string(
        server=server,
        database=database,
        user=user,
        password=password,
    )

    engine_options = {
        "pool_pre_ping": True,
    }

    if autocommit:
        engine_options["isolation_level"] = "AUTOCOMMIT"

    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={connection_params}",
        **engine_options,
    )


def validate_database_name(
    database_name: str,
) -> None:
    """
    Validate the database name before using it
    in a CREATE DATABASE statement.
    """

    if not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*",
        database_name,
    ):
        raise ValueError(
            f"Invalid database name: '{database_name}'. "
            "Only letters, numbers, and underscores are allowed."
        )


def split_sql_batches(
    sql_script: str,
) -> list[str]:
    """
    Split a SQL Server script using GO batch separators.

    GO is treated as a separator only when it appears
    alone on a line.
    """

    batches = re.split(
        r"^\s*GO\s*;?\s*$",
        sql_script,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    return [
        batch.strip()
        for batch in batches
        if batch.strip()
    ]


def execute_database_config(
    master_engine: Engine,
    config_file: Path,
    target_db: str,
) -> None:
    """
    Execute SQL Server and database configuration.

    The database name is read from DB_NAME in .env
    and injected into the SQL configuration template.
    """

    if not config_file.exists():
        raise FileNotFoundError(
            "Database configuration file was not found: "
            f"{config_file}"
        )

    if not config_file.is_file():
        raise ValueError(
            "Database configuration path is not a file: "
            f"{config_file}"
        )

  
    validate_database_name(target_db)

    logger.info("=" * 60)
    logger.info(
        "PHASE 2: SQL SERVER AND DATABASE CONFIGURATION"
    )
    logger.info("=" * 60)

    logger.info(
        "Configuration file: %s",
        config_file,
    )

   
    sql_script = config_file.read_text(
        encoding="utf-8-sig"
    )

    sql_script = sql_script.replace(
        "{{DB_NAME}}",
        target_db,
    )

    if "{{DB_NAME}}" in sql_script:
        raise ValueError(
            "The database name placeholder was not replaced."
        )

    sql_batches = split_sql_batches(
        sql_script
    )

    if not sql_batches:
        raise ValueError(
            f"Database configuration file is empty: "
            f"{config_file}"
        )


    with master_engine.connect() as conn:
        for batch_number, sql_batch in enumerate(
            sql_batches,
            start=1,
        ):
            logger.info(
                "Executing database configuration batch %s...",
                batch_number,
            )

            conn.exec_driver_sql(
                sql_batch
            )

    
    logger.info(
        "SQL Server and database configuration "
        "completed successfully for database '%s'.",
        target_db,
    )


def execute_schema_files(
    target_engine: Engine,
    schema_folder: Path,
) -> None:
    """
    Execute schema files 00 through 06 sequentially
    inside the target database.
    """

    missing_files = [
        file_name
        for file_name in SCHEMA_FILES
        if not (
            schema_folder / file_name
        ).exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Missing required schema files: "
            + ", ".join(missing_files)
        )

    logger.info("=" * 60)
    logger.info(
        "PHASE 3: STAR SCHEMA INITIALIZATION"
    )
    logger.info("=" * 60)

    logger.info(
        "SQL schema directory: %s",
        schema_folder,
    )

    logger.info(
        "Found %s required schema files.",
        len(SCHEMA_FILES),
    )

   
    with target_engine.begin() as conn:
        for file_name in SCHEMA_FILES:
            file_path = (
                schema_folder
                / file_name
            )

            logger.info(
                "Executing schema script: %s",
                file_name,
            )

            sql_script = file_path.read_text(
                encoding="utf-8-sig"
            )

            sql_batches = split_sql_batches(
                sql_script
            )

            if not sql_batches:
                raise ValueError(
                    f"Schema file is empty: {file_path}"
                )

            for batch_number, sql_batch in enumerate(
                sql_batches,
                start=1,
            ):
                try:
                    conn.exec_driver_sql(
                        sql_batch
                    )

                except Exception as error:
                    raise RuntimeError(
                        f"Failed to execute batch "
                        f"{batch_number} in "
                        f"{file_name}: {error}"
                    ) from error

            logger.info(
                "Schema script completed: %s",
                file_name,
            )


def setup_infrastructure() -> bool:
    """
    Initialize the SQL Server database infrastructure.

    Execution order:
        1. Read configuration from .env.
        2. Create or verify the target database.
        3. Run 07_config_database.sql using master
           with AUTOCOMMIT.
        4. Run schema files 00 through 06 inside
           the target database.
    """

   
    server = os.getenv("DB_SERVER")
    target_db = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")

    missing_variables = []

    if not server:
        missing_variables.append("DB_SERVER")

    if not target_db:
        missing_variables.append("DB_NAME")

    if not db_user:
        missing_variables.append("DB_USER")

    if not db_pass:
        missing_variables.append("DB_PASS")

    if missing_variables:
        logger.error(
            "Infrastructure initialization aborted. "
            "Missing environment variables: %s",
            ", ".join(missing_variables),
        )
        return False

    try:
        validate_database_name(
            target_db
        )

    except ValueError as error:
        logger.error(
            "%s",
            error,
        )
        return False

   
    src_directory = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    schema_folder = (
        src_directory
        / "sql_model"
    )

 
    config_file = (
        schema_folder
        / "sql_config"
        / "07_config_database.sql"
    )

    logger.info("=" * 60)
    logger.info(
        "PHASE 1: AUTOMATED DB & SCHEMA "
        "INFRASTRUCTURE INITIALIZATION"
    )
    logger.info("=" * 60)

    master_engine = None
    target_engine = None

    try:
       
        master_engine = create_sql_engine(
            server=server,
            database="master",
            user=db_user,
            password=db_pass,
            autocommit=True,
        )

        
        with master_engine.connect() as conn:
            database_exists = conn.execute(
                text(
                    """
                    SELECT 1
                    FROM sys.databases
                    WHERE name = :database_name
                    """
                ),
                {
                    "database_name": target_db,
                },
            ).scalar()

            if database_exists:
                logger.info(
                    "Database '%s' already exists. "
                    "Skipping creation step.",
                    target_db,
                )

            else:
                logger.info(
                    "Database '%s' does not exist. "
                    "Creating database...",
                    target_db,
                )

                # target_db has already been validated.
                safe_database_name = (
                    f"[{target_db}]"
                )

                conn.exec_driver_sql(
                    f"CREATE DATABASE {safe_database_name}"
                )

                logger.info(
                    "Database '%s' was created successfully.",
                    target_db,
                )

        
        execute_database_config(
            master_engine=master_engine,
            config_file=config_file,
            target_db=target_db
        )

      
        if not schema_folder.exists():
            logger.error(
                "SQL schema directory was not found: %s",
                schema_folder,
            )
            return False

        if not schema_folder.is_dir():
            logger.error(
                "SQL schema path is not a directory: %s",
                schema_folder,
            )
            return False

       
        target_engine = create_sql_engine(
            server=server,
            database=target_db,
            user=db_user,
            password=db_pass,
            autocommit=False,
        )

       
        execute_schema_files(
            target_engine=target_engine,
            schema_folder=schema_folder,
        )

        logger.info("=" * 60)
        logger.info(
            "DATABASE INFRASTRUCTURE "
            "INITIALIZED SUCCESSFULLY!✅"
        )
        logger.info(
            "Database configuration, schema tables, "
            "indexes, and stored procedures are ready."
        )
        logger.info("=" * 60)

        return True

    except Exception as error:
        logger.error(
            "Fatal error during infrastructure setup: %s",
            error,
            exc_info=True,
        )
        return False

    finally:
        if target_engine is not None:
            target_engine.dispose()

        if master_engine is not None:
            master_engine.dispose()


if __name__ == "__main__":
    setup_infrastructure()