from pydantic import BaseModel, Field
from typing import Optional


class LoanApplication(BaseModel):
    """Schema đầu vào cho một hồ sơ vay."""
    person_age: int = Field(..., example=28, description="Tuổi khách hàng")
    person_income: float = Field(..., example=65000, description="Thu nhập hàng năm ($)")
    person_home_ownership: str = Field(..., example="RENT", description="Sở hữu nhà (RENT, OWN, MORTGAGE, OTHER)")
    person_emp_length: float = Field(..., example=4.0, description="Số năm làm việc")
    loan_intent: str = Field(..., example="PERSONAL", description="Mục đích vay")
    loan_grade: str = Field(..., example="B", description="Hạng tín dụng (A-G)")
    loan_amnt: float = Field(..., example=10000, description="Số tiền vay ($)")
    loan_int_rate: float = Field(..., example=11.14, description="Lãi suất (%) — do khách hàng đề xuất")
    loan_percent_income: float = Field(..., example=0.15, description="Tỷ lệ nợ/thu nhập")
    cb_person_default_on_file: str = Field(..., example="N", description="Lịch sử vỡ nợ (Y/N)")
    cb_person_cred_hist_length: int = Field(..., example=3, description="Độ dài lịch sử tín dụng (năm)")
    loan_term_months: int = Field(36, example=36, description="Kỳ hạn khoản vay (tháng: 12, 24, 36, 48, 60)")

    # Các trường bổ sung (optional với giá trị mặc định)
    gender: Optional[str] = Field("MALE", example="MALE")
    marital_status: Optional[str] = Field("SINGLE", example="SINGLE")
    education_level: Optional[str] = Field("BACHELOR", example="BACHELOR")
    employment_type: Optional[str] = Field("FULL_TIME", example="FULL_TIME")
    loan_to_income_ratio: Optional[float] = Field(0.15, example=0.15)
    debt_to_income_ratio: Optional[float] = Field(0.25, example=0.25)
    credit_utilization_ratio: Optional[float] = Field(0.35, example=0.35)
    past_delinquencies: Optional[int] = Field(0, example=0)


class RiskBasedPricingRecommendation(BaseModel):
    """Schema kết quả định giá lãi suất cá nhân hóa (Risk-Based Pricing Engine).
    """
    # ── Lãi suất cá nhân hóa & cấu phần Waterfall ──────────────────────────
    recommended_interest_rate: float = Field(
        ...,
        description="Lãi suất cá nhân hóa được đề xuất (% / năm). "
                    "APR = Base Rate + Risk Spread + Capital Discount + Intent Adjustment"
    )
    base_rate: float = Field(
        ...,
        description="Lãi suất cơ sở (Cost of Funds + Operating Margin), mặc định 6.5%"
    )
    risk_spread: float = Field(
        ...,
        description="Biên độ bù rủi ro theo Risk Tier (Δr_risk). "
                    "LOW: +1.0%, MEDIUM_LOW: +2.5%, MEDIUM_HIGH: +5.0%, HIGH: +9.0%"
    )
    capital_discount: float = Field(
        ...,
        description="Chiết khấu sở hữu nhà (Δr_capital). "
                    "OWN: -0.5%, MORTGAGE: -0.25%, RENT/OTHER: 0.0%"
    )
    intent_adjustment: float = Field(
        ...,
        description="Hiệu chỉnh mục đích vay (Δr_intent). "
                    "EDUCATION: -0.3%, VENTURE: +0.5%, DEBTCONSOLIDATION: +0.8%"
    )

    # ── Hạn mức tín dụng động ───────────────────────────────────────────────
    max_credit_limit: float = Field(
        ...,
        description="Hạn mức tín dụng tối đa ngân hàng khuyến nghị cấp ($). "
                    "= min(Annual Income × LTI Multiple, Hard Cap)"
    )
    requested_amount: float = Field(
        ...,
        description="Số tiền vay khách hàng đề xuất ($)"
    )
    limit_status: str = Field(
        ...,
        description="Trạng thái hạn mức: WITHIN_LIMIT | EXCEEDS_RECOMMENDED_LIMIT | REJECTED"
    )

    # ── Mô phỏng trả góp định kỳ (Amortization PMT) ─────────────────────────
    loan_term_months: Optional[int] = Field(
        36,
        description="Kỳ hạn khoản vay (tháng), mặc định 36 tháng"
    )
    monthly_payment_estimate: Optional[float] = Field(
        0.0,
        description="Số tiền trả góp hàng tháng ước tính ($). "
                    "PMT = P × [r(1+r)^n / ((1+r)^n - 1)]"
    )
    total_interest_estimate: Optional[float] = Field(
        0.0,
        description="Tổng tiền lãi phải trả trong suốt kỳ vay ($). "
                    "= Monthly Payment × n - Principal"
    )


class CreditRiskAssessment(BaseModel):
    """Kết quả đánh giá rủi ro tín dụng toàn diện từ mô hình ML."""
    pd_score: float = Field(..., description="Xác suất nợ xấu (0.0 – 1.0)")
    credit_score: int = Field(..., description="Điểm tín dụng FICO (300 – 850)")
    risk_tier: str = Field(..., description="Phân hạng rủi ro (LOW / MEDIUM_LOW / MEDIUM_HIGH / HIGH)")
    decision: str = Field(..., description="Quyết định tín dụng (APPROVED / APPROVED_CONDITIONAL / MANUAL_REVIEW / REJECTED)")
    contributions: Optional[dict] = Field(None, description="Điểm đóng góp WoE của từng biến")
    top_factors: Optional[dict] = Field(None, description="Top yếu tố tích cực và tiêu cực")
    pricing_recommendation: Optional[RiskBasedPricingRecommendation] = Field(
        None,
        description="Gói định giá lãi suất cá nhân hóa và hạn mức tín dụng động"
    )


class PredictApiResponse(BaseModel):
    """Phản hồi chuẩn của API endpoint POST /api/v1/predict."""
    success: bool = Field(True)
    task: str = Field("credit_risk")
    credit_risk_assessment: CreditRiskAssessment


class EnrichPayload(BaseModel):
    """Payload gửi lên để lưu hồ sơ vào tập dữ liệu."""
    application: LoanApplication
    loan_status: int = Field(
        -1, ge=-1, le=1,
        description="Nhãn thực tế: -1=Chưa gán nhãn, 0=Trả nợ tốt, 1=Nợ xấu"
    )
    ml_pd_score: float = Field(..., description="Xác suất nợ xấu từ mô hình ML")
    ml_credit_score: int = Field(..., description="Điểm tín dụng FICO từ mô hình ML")
    ml_decision: str = Field(..., description="Quyết định từ mô hình ML")
