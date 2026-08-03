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
    loan_int_rate: float = Field(..., example=11.14, description="Lãi suất (%)")
    loan_percent_income: float = Field(..., example=0.15, description="Tỷ lệ nợ/thu nhập")
    cb_person_default_on_file: str = Field(..., example="N", description="Lịch sử vỡ nợ (Y/N)")
    cb_person_cred_hist_length: int = Field(..., example=3, description="Độ dài lịch sử tín dụng (năm)")

    # Các trường bổ sung (optional với giá trị mặc định)
    gender: Optional[str] = Field("MALE", example="MALE")
    marital_status: Optional[str] = Field("SINGLE", example="SINGLE")
    education_level: Optional[str] = Field("BACHELOR", example="BACHELOR")
    employment_type: Optional[str] = Field("FULL_TIME", example="FULL_TIME")
    loan_to_income_ratio: Optional[float] = Field(0.15, example=0.15)
    debt_to_income_ratio: Optional[float] = Field(0.25, example=0.25)
    credit_utilization_ratio: Optional[float] = Field(0.35, example=0.35)
    past_delinquencies: Optional[int] = Field(0, example=0)


class EnrichPayload(BaseModel):
    """Payload gửi lên để lưu hồ sơ vào tập dữ liệu."""
    application: LoanApplication
    loan_status: int = Field(
        -1, ge=-1, le=1,
        description="Nhãn thực tế: -1=Chưa gán nhãn, 0=Trả nợ tốt, 1=Nợ xấu"
    )
    ai_pd_score: float = Field(..., description="Xác suất nợ xấu từ mô hình AI")
    ai_credit_score: int = Field(..., description="Điểm tín dụng FICO từ mô hình AI")
    ai_decision: str = Field(..., description="Quyết định từ mô hình AI")
