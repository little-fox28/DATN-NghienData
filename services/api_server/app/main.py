"""
backend/main.py — FastAPI Loan Collection API & ML Scoring Endpoint
Chạy ứng dụng: python -m services.api_server.app.main
"""
import sys
from pathlib import Path

# Thêm root directory vào sys.path để import dễ dàng
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from services.api_server.app.config import HOST, PORT
from services.ml_engine.src.machine_learning.config import get_task_config
from services.ml_engine.src.machine_learning.predict import ModelPredictor

from fastapi.middleware.cors import CORSMiddleware

# Khởi tạo sẵn ModelPredictor cho bài toán mặc định (Credit Risk) khi khởi động API
try:
    default_config = get_task_config("credit_risk")
    default_config["task_name"] = "credit_risk"
    default_predictor = ModelPredictor(default_config)
except Exception as err:
    default_predictor = None

app = FastAPI(
    title="Loan Application & Credit Risk API",
    description="API thu thập thông tin khoản vay và tính toán điểm tín dụng (ML Core)",
    version="1.0.0",
)

# Cấu hình CORS để Frontend (React/Vite) gọi API không bị lỗi Preflight OPTIONS 405
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Schema nhận dữ liệu đơn xin vay
class LoanApplication(BaseModel):
    person_age: int = Field(..., json_schema_extra={"example": 28}, description="Tuổi khách hàng")
    person_income: float = Field(..., json_schema_extra={"example": 65000}, description="Thu nhập hàng năm ($)")
    person_home_ownership: str = Field(..., json_schema_extra={"example": "RENT"}, description="Sở hữu nhà (RENT, OWN, MORTGAGE, OTHER)")
    person_emp_length: float = Field(..., json_schema_extra={"example": 4.0}, description="Số năm làm việc")
    loan_intent: str = Field(..., json_schema_extra={"example": "PERSONAL"}, description="Mục đích vay")
    loan_grade: str = Field(..., json_schema_extra={"example": "B"}, description="Hạng tín dụng (A-G)")
    loan_amnt: float = Field(..., json_schema_extra={"example": 10000}, description="Số tiền vay ($)")
    loan_int_rate: float = Field(..., json_schema_extra={"example": 11.14}, description="Lãi suất (%)")
    loan_percent_income: float = Field(..., json_schema_extra={"example": 0.15}, description="Tỷ lệ nợ/thu nhập")
    cb_person_default_on_file: str = Field(..., json_schema_extra={"example": "N"}, description="Lịch sử vỡ nợ (Y/N)")
    cb_person_cred_hist_length: int = Field(..., json_schema_extra={"example": 3}, description="Độ dài lịch sử tín dụng (năm)")

    # Các trường bổ sung
    gender: Optional[str] = Field("MALE", json_schema_extra={"example": "MALE"})
    marital_status: Optional[str] = Field("SINGLE", json_schema_extra={"example": "SINGLE"})
    education_level: Optional[str] = Field("BACHELOR", json_schema_extra={"example": "BACHELOR"})
    employment_type: Optional[str] = Field("FULL_TIME", json_schema_extra={"example": "FULL_TIME"})
    loan_to_income_ratio: Optional[float] = Field(0.15, json_schema_extra={"example": 0.15})
    debt_to_income_ratio: Optional[float] = Field(0.25, json_schema_extra={"example": 0.25})
    credit_utilization_ratio: Optional[float] = Field(0.35, json_schema_extra={"example": 0.35})
    past_delinquencies: Optional[int] = Field(0, json_schema_extra={"example": 0})


@app.get("/")
def root():
    return {
        "service": "Loan Collection & Credit Risk API",
        "status": "online",
        "documentation": f"http://{HOST}:{PORT}/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/predict", summary="Chấm điểm tín dụng cho một hồ sơ vay")
def predict_credit_risk(application: LoanApplication, task: str = "credit_risk"):
    """
    Nhận thông tin khoản vay từ Client/App, gọi lõi ML `src.machine_learning` để tính toán:
    - PD Score (Xác suất vỡ nợ)
    - Credit Score (Điểm tín dụng 300 - 850)
    - Risk Tier (Nhóm rủi ro: LOW, MEDIUM, HIGH, CRITICAL)
    - Decision (Quyết định: APPROVED, MANUAL_REVIEW, REJECTED)
    """
    try:
        record = application.model_dump()
        
        # Chọn predictor theo task
        if task == "credit_risk" and default_predictor is not None:
            result = default_predictor.score_single(record)
        else:
            task_cfg = get_task_config(task)
            task_cfg["task_name"] = task
            custom_predictor = ModelPredictor(task_cfg)
            result = custom_predictor.score_single(record)

        return {
            "success": True,
            "task": task,
            "application_summary": {
                "income": application.person_income,
                "loan_amount": application.loan_amnt,
                "intent": application.loan_intent
            },
            "credit_risk_assessment": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán ML: {str(e)}")


if __name__ == "__main__":
    print(f"🚀 Starting Loan Collection API on http://{HOST}:{PORT}")
    print(f"📖 Swagger Docs available at http://{HOST}:{PORT}/docs")
    uvicorn.run("services.api_server.app.main:app", host=HOST, port=PORT, reload=True)
