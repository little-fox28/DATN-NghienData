"""
Router: /api/v1/analytics — Portfolio Analytics & Executive Summary for Dashboard
"""
from fastapi import APIRouter, HTTPException
from services.api_server.app.services import analytics as analytics_svc

router = APIRouter(prefix="/api/v1/analytics", tags=["Portfolio Analytics"])

@router.get("/portfolio-summary", summary="Lấy thống kê tổng quan danh mục tín dụng")
def get_portfolio_summary():
    """Trả về toàn bộ KPI, phân bổ Risk Tiers, Loan Grades, Terms, Intents cho Dashboard."""
    try:
        data = analytics_svc.get_portfolio_summary()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính toán thống kê danh mục: {e}")
