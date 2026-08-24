"""
Router: /api/v1/predict — ML Credit Risk Scoring
"""
from fastapi import APIRouter, HTTPException
from services.api_server.app.schemas.loan import LoanApplication
from services.api_server.app.services.predictor import score_application

router = APIRouter(prefix="/api/v1", tags=["Credit Risk Scoring"])


@router.post("/predict", summary="Chấm điểm tín dụng cho một hồ sơ vay")
def predict_credit_risk(application: LoanApplication, task: str = "credit_risk"):
    try:
        from services.api_server.app.services.enrich import read_all_records
        from services.api_server.app.utils.hash_utils import get_next_client_id, generate_application_id

        app_data = application.model_dump()
        result = score_application(app_data, task)

        existing_count = len(read_all_records())
        client_id = application.client_ID or get_next_client_id(offset=existing_count)
        application_id = generate_application_id(client_id, channel="O")

        return {
            "success": True,
            "task": task,
            "client_id": client_id,
            "application_id": application_id,
            "application_summary": {
                "income":      application.person_income,
                "loan_amount": application.loan_amnt,
                "intent":      application.loan_intent,
            },
            "credit_risk_assessment": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán ML: {e}")
