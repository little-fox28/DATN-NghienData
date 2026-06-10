import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.utils.logger import get_logger

# Tải biến môi trường từ file .env
load_dotenv()
logger = get_logger(__name__)

def build_connection_string(server: str, database: str, user: str, password: str) -> str:
    """
    Hàm hỗ trợ tự động cấu hình chuỗi kết nối (Connection String).
    - Nếu có điền DB_USER và DB_PASS: Dùng SQL Server Authentication.
    - Nếu để trống: Tự động lùi về Windows Authentication (Trusted_Connection).
    """
    if user and password:
        return urllib.parse.quote_plus(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={user};'
            f'PWD={password};'
            f'TrustServerCertificate=yes;'
        )
    else:
        return urllib.parse.quote_plus(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'Trusted_Connection=yes;'
            f'TrustServerCertificate=yes;'
        )

def setup_infrastructure() -> None:
    # 1. ĐỌC CẤU HÌNH TỪ FILE .ENV
    server = os.getenv("DB_SERVER")
    target_db = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")

    if not server or not target_db:
        logger.error("Thiếu cấu hình DB_SERVER hoặc DB_NAME trong file .env!")
        return

    logger.info("=" * 60)
    logger.info("GIAI ĐOẠN 1: TỰ ĐỘNG KHỞI TẠO HẠ TẦNG DB & SCHEMA VỚI CẤU TRÚC ĐA FILE")
    logger.info("=" * 60)

    # 2. KẾT NỐI VÀO DATABASE HỆ THỐNG 'MASTER' ĐỂ KIỂM TRA & TẠO DATABASE MỚI
    # Bật isolation_level="AUTOCOMMIT" để giải phóng transaction block khi chạy lệnh CREATE DATABASE
    master_params = build_connection_string(server, 'master', db_user, db_pass)
    master_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={master_params}", isolation_level="AUTOCOMMIT")

    try:
        with master_engine.connect() as conn:
            # Kiểm tra xem Database mục tiêu đã tồn tại trong hệ thống chưa (Idempotency)
            db_exists = conn.execute(
                text(f"SELECT 1 FROM sys.databases WHERE name = :db_name"), 
                {"db_name": target_db}
            ).scalar()
            
            if not db_exists:
                logger.info(f"Database '{target_db}' chưa tồn tại. Tiến hành khởi tạo...")
                conn.execute(text(f"CREATE DATABASE {target_db}"))
                logger.info(f"Tạo thành công cơ sở dữ liệu: '{target_db}'")
            else:
                logger.info(f" Database '{target_db}' đã tồn tại sẵn. Bỏ qua bước tạo mới.")
    except Exception as e:
        logger.error(f"Thất bại khi khởi tạo Database hệ thống: {e}")
        return

    # 3. QUÉT THƯ MỤC SQL_MODELS VÀ THỰC THI TUẦN TỰ FILE TỪ 00 -> 06
    target_params = build_connection_string(server, target_db, db_user, db_pass)
    target_engine = create_engine(f"mssql+pyodbc:///?odbc_connect={target_params}")
    # 1. Lấy tọa độ gốc của toàn bộ dự án
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    
    schema_folder = None
    logger.info(f"Đang bật Radar quét toàn bộ thư mục: {project_root} ...")

    # 2. Bật Radar dò tìm file SQL
    for root_dir, dirs, files in os.walk(project_root):
        if "00_stg_loan.sql" in files:
            schema_folder = root_dir  # Bắt được mục tiêu, lưu lại đường dẫn thật!
            break

    # 3. Kiểm tra kết quả dò tìm
    if not schema_folder:
        logger.error(f"TUYỆT VỌNG: Không tìm thấy file '00_stg_loan.sql' ở bất kỳ đâu!")
        return

    logger.info(f"Đã dò trúng mục tiêu! Tên thật sự của thư mục SQL là: {schema_folder}")

    if not os.path.exists(schema_folder):
        logger.error(f"Không tìm thấy thư mục chứa các file thiết kế: {schema_folder}/")
        return

    try:
        # Nhặt toàn bộ file .sql có trong thư mục và sắp xếp theo bảng chữ cái/chữ số (00 -> 06)
        sql_files = sorted([f for f in os.listdir(schema_folder) if f.endswith('.sql')])
        
        if not sql_files:
            logger.warning(f"Thư mục '{schema_folder}' đang trống. Không tìm thấy tệp .sql nào để khởi tạo.")
            return

        logger.info(f"Tìm thấy {len(sql_files)} file cấu trúc. Bắt đầu nạp tuần tự...")

        # Mở kết nối vào Database vừa được setup sạch sẽ
        with target_engine.connect() as conn:
            for file_name in sql_files:
                file_path = os.path.join(schema_folder, file_name)
                logger.info(f"Đang thực thi: {file_name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()

                # Tách lô lệnh bằng từ khóa 'GO' (vì SQLAlchemy không hỗ trợ chạy hàng loạt cụm GO của SQL Server)
                statements = sql_script.split('GO')
                for statement in statements:
                    if statement.strip():  # Loại bỏ khoảng trắng hoặc dòng trống thừa thãi
                        conn.execute(text(statement))
            
            # Lưu lại toàn bộ thay đổi (Tạo các bảng tĩnh và Stored Procedure) vào hệ thống
            conn.commit()
            logger.info("=" * 60)
            logger.info("Xây dựng thành công toàn bộ Vỏ bảng và Stored Procedure!")
            logger.info("Hạ tầng đã sẵn sàng. Bạn có thể kích hoạt file main.py để đổ dữ liệu.")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng khi nạp cấu trúc Schema: {e}", exc_info=True)

if __name__ == "__main__":
    setup_infrastructure()