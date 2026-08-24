import zlib
from datetime import datetime

RAW_DATA_BASE_COUNT = 32581


def get_next_client_id(offset: int = 0) -> str:
    """Sinh mã khách hàng tuần tự tiếp nối tệp gốc (CUST_32582, CUST_32583...)."""
    next_index = RAW_DATA_BASE_COUNT + offset + 1
    return f"CUST_{next_index:05d}"


def generate_application_id(client_id: str, channel: str = "O") -> str:
    """
    Sinh Mã Hồ sơ Vay chuẩn hóa: LN-{CHANNEL}{YYMMDD}-{CLIENT_SHORT}-{CRC16}
    Ví dụ: LN-O260824-C32582-A8F2
    """
    now = datetime.now()
    date_str = now.strftime("%y%m%d")
    clean_client = client_id.replace("CUST_", "C") if "CUST_" in client_id else client_id
    payload = f"{channel}|{date_str}|{client_id}|{now.microsecond}"
    checksum = f"{zlib.crc32(payload.encode('utf-8')) & 0xFFFF:04X}"
    return f"LN-{channel}{date_str}-{clean_client}-{checksum}"


