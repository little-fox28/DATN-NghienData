"""
Router: /api/v1/predict — ML Credit Risk Scoring
"""
from fastapi import APIRouter, HTTPException
from services.api_server.app.schemas.loan import LoanApplication
from services.api_server.app.services.predictor import score_application

router = APIRouter(prefix="/api/v1", tags=["Credit Risk Scoring"])


@router.post("/predict", summary="Chấm điểm tín dụng cho một hồ sơ vay")
def predict_credit_risk(application: LoanApplication, task: str = "credit_risk"):
    """
    Nhận thông tin khoản vay, gọi ML core để tính toán:
    - PD Score (Xác suất vỡ nợ)
    - Credit Score (300–850)
    - Risk Tier (LOW / MEDIUM / HIGH / CRITICAL)
    - Decision (APPROVED / MANUAL_REVIEW / REJECTED)
    """
    try:
        result = score_application(application.model_dump(), task)
        return {
            "success": True,
            "task": task,
            "application_summary": {
                "income":      application.person_income,
                "loan_amount": application.loan_amnt,
                "intent":      application.loan_intent,
            },
            "credit_risk_assessment": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán ML: {e}")
