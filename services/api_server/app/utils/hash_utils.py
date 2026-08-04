import hashlib
import hmac
import os
from datetime import datetime

# Sử dụng biến môi trường cho Secret Key, nếu không có thì dùng giá trị mặc định cho dev
SECRET_KEY = os.getenv("CLIENT_HASH_SECRET", "credit-risk-default-secret-key").encode()

def generate_client_id(app_data: dict) -> str:
    """
    Tạo Client ID bằng thuật toán HMAC-SHA256.
    Lấy ra chuỗi hex 32 ký tự để đảm bảo giả danh hóa và tính duy nhất.
    """
    # Ghép các trường thông tin cơ bản kết hợp timestamp để đảm bảo ID không trùng lặp (duy nhất)
    raw_string = "|".join([
        str(app_data.get("person_age", "")),
        str(app_data.get("gender", "")),
        str(app_data.get("person_income", "")),
        str(app_data.get("education_level", "")),
        datetime.now().isoformat(),
    ])
    
    # Băm dữ liệu bằng HMAC-SHA256 (tổng độ dài là 64 ký tự hex)
    # Lấy 32 ký tự đầu tiên theo yêu cầu
    digest = hmac.new(
        SECRET_KEY, 
        raw_string.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest()[:32].upper()
    
    return f"ENRICH_{digest}"
