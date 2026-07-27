import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { StepWizard } from './components/StepWizard';
import { CreditScoreGauge } from './components/CreditScoreGauge';
import type { LoanApplicationData, PredictApiResponse } from './types/loan';
import { predictCreditRisk } from './api/client';
import { ArrowRight, ArrowLeft, Send, RefreshCw, AlertCircle } from 'lucide-react';

const initialFormData: LoanApplicationData = {
  // Step 1
  person_age: 28,
  gender: 'MALE',
  education_level: 'BACHELOR',
  marital_status: 'SINGLE',

  // Step 2
  person_income: 65000,
  person_home_ownership: 'RENT',
  person_emp_length: 4.0,
  employment_type: 'FULL_TIME',
  cb_person_default_on_file: 'N',
  cb_person_cred_hist_length: 3,
  past_delinquencies: 0,

  // Step 3
  loan_intent: 'PERSONAL',
  loan_grade: 'B',
  loan_amnt: 10000,
  loan_int_rate: 11.14,
  loan_percent_income: 0.15,
  loan_to_income_ratio: 0.15,
  debt_to_income_ratio: 0.25,
  credit_utilization_ratio: 0.35,
};

export const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [formData, setFormData] = useState<LoanApplicationData>(initialFormData);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictApiResponse | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleNext = () => {
    setCurrentStep((prev) => Math.min(prev + 1, 4));
  };

  const handlePrev = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      // Tự động tính lại tỷ lệ nợ/thu nhập trước khi gửi API
      const updatedData = {
        ...formData,
        loan_percent_income: formData.person_income > 0 
          ? Number((formData.loan_amnt / formData.person_income).toFixed(2)) 
          : 0,
        loan_to_income_ratio: formData.person_income > 0 
          ? Number((formData.loan_amnt / formData.person_income).toFixed(2)) 
          : 0,
      };
      
      const apiResult = await predictCreditRisk(updatedData, 'credit_risk');
      setResult(apiResult);
      setCurrentStep(4);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail || 
        'Không thể kết nối với FastAPI Server (http://127.0.0.1:8000). Vui lòng kiểm tra Server đã khởi động chưa.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData(initialFormData);
    setResult(null);
    setError(null);
    setCurrentStep(1);
  };

  return (
    <>
      <Navbar />

      <main className="main-container">
        <StepWizard currentStep={currentStep} onStepClick={(step) => setCurrentStep(step)} />

        <div className="glass-card">
          {error && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#F87171', padding: '1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* STEP 1: Personal Demographics */}
          {currentStep === 1 && (
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '0.5rem' }}>
                Bước 1: Thông tin Nhân khẩu học
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Thu thập các thuộc tính định danh cá nhân của người nộp đơn vay.
              </p>

              <div className="form-grid">
                <div className="form-group">
                  <label>Độ tuổi khách hàng (person_age)</label>
                  <input
                    type="number"
                    name="person_age"
                    className="form-control"
                    value={formData.person_age}
                    onChange={handleChange}
                    min={18}
                    max={85}
                  />
                </div>

                <div className="form-group">
                  <label>Giới tính (gender)</label>
                  <select name="gender" className="form-control" value={formData.gender} onChange={handleChange}>
                    <option value="MALE">Nam (MALE)</option>
                    <option value="FEMALE">Nữ (FEMALE)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Trình độ Học vấn (education_level)</label>
                  <select name="education_level" className="form-control" value={formData.education_level} onChange={handleChange}>
                    <option value="HIGH_SCHOOL">Trung học (HIGH_SCHOOL)</option>
                    <option value="BACHELOR">Cử nhân (BACHELOR)</option>
                    <option value="MASTER">Thạc sĩ (MASTER)</option>
                    <option value="DOCTORATE">Tiến sĩ (DOCTORATE)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Tình trạng Hôn nhân (marital_status)</label>
                  <select name="marital_status" className="form-control" value={formData.marital_status} onChange={handleChange}>
                    <option value="SINGLE">Độc thân (SINGLE)</option>
                    <option value="MARRIED">Đã kết hôn (MARRIED)</option>
                    <option value="DIVORCED">Đã ly hôn (DIVORCED)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Financial & Employment */}
          {currentStep === 2 && (
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '0.5rem' }}>
                Bước 2: Năng lực Tài chính & Lịch sử Tín dụng
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Khai báo thu nhập, thâm niên việc làm và lịch sử ghi nhận nợ xấu trên CIC.
              </p>

              <div className="form-grid">
                <div className="form-group">
                  <label>Thu nhập Hàng năm ($) (person_income)</label>
                  <input
                    type="number"
                    name="person_income"
                    className="form-control"
                    value={formData.person_income}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label>Sở hữu Nhà ở (person_home_ownership)</label>
                  <select name="person_home_ownership" className="form-control" value={formData.person_home_ownership} onChange={handleChange}>
                    <option value="RENT">Thuê nhà (RENT)</option>
                    <option value="OWN">Sở hữu riêng (OWN)</option>
                    <option value="MORTGAGE">Thế chấp (MORTGAGE)</option>
                    <option value="OTHER">Khác (OTHER)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Thâm niên Làm việc (Năm) (person_emp_length)</label>
                  <input
                    type="number"
                    name="person_emp_length"
                    className="form-control"
                    value={formData.person_emp_length}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label>Từng có Lịch sử Nợ xấu trên CIC? (default_on_file)</label>
                  <select name="cb_person_default_on_file" className="form-control" value={formData.cb_person_default_on_file} onChange={handleChange}>
                    <option value="N">Không (N - No)</option>
                    <option value="Y">Có nợ xấu (Y - Yes)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Độ dài Lịch sử Tín dụng (Năm) (cred_hist_length)</label>
                  <input
                    type="number"
                    name="cb_person_cred_hist_length"
                    className="form-control"
                    value={formData.cb_person_cred_hist_length}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Loan Details */}
          {currentStep === 3 && (
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '0.5rem' }}>
                Bước 3: Chi tiết Đơn xin Vay
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Nhập số tiền vay, hạng rủi ro dự kiến và mục đích sử dụng vốn.
              </p>

              <div className="form-grid">
                <div className="form-group">
                  <label>Số tiền xin vay ($) (loan_amnt)</label>
                  <input
                    type="number"
                    name="loan_amnt"
                    className="form-control"
                    value={formData.loan_amnt}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label>Mục đích Vay (loan_intent)</label>
                  <select name="loan_intent" className="form-control" value={formData.loan_intent} onChange={handleChange}>
                    <option value="PERSONAL">Vay Tiêu dùng (PERSONAL)</option>
                    <option value="EDUCATION">Vay Học tập (EDUCATION)</option>
                    <option value="MEDICAL">Vay Y tế (MEDICAL)</option>
                    <option value="VENTURE">Vay Kinh doanh (VENTURE)</option>
                    <option value="HOMEIMPROVEMENT">Sửa chữa Nhà (HOMEIMPROVEMENT)</option>
                    <option value="DEBTCONSOLIDATION">Gộp nợ (DEBTCONSOLIDATION)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Hạng Khoản vay (loan_grade A-G)</label>
                  <select name="loan_grade" className="form-control" value={formData.loan_grade} onChange={handleChange}>
                    <option value="A">Grade A (An toàn nhất)</option>
                    <option value="B">Grade B</option>
                    <option value="C">Grade C</option>
                    <option value="D">Grade D</option>
                    <option value="E">Grade E</option>
                    <option value="F">Grade F</option>
                    <option value="G">Grade G (Rủi ro cao)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Lãi suất Đề xuất (%) (loan_int_rate)</label>
                  <input
                    type="number"
                    step="0.01"
                    name="loan_int_rate"
                    className="form-control"
                    value={formData.loan_int_rate}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: AI Decision Result */}
          {currentStep === 4 && result && (
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#FFFFFF', marginBottom: '1rem', textAlign: 'center' }}>
                Kết quả Phê duyệt & Chấm điểm Tín dụng (AI Engine)
              </h2>

              <CreditScoreGauge
                score={result.credit_risk_assessment.credit_score}
                pdScore={result.credit_risk_assessment.pd_score}
                riskTier={result.credit_risk_assessment.risk_tier}
                decision={result.credit_risk_assessment.decision}
              />
            </div>
          )}

          {/* Action Buttons */}
          <div className="btn-group">
            {currentStep > 1 && currentStep < 4 && (
              <button type="button" className="btn btn-secondary" onClick={handlePrev}>
                <ArrowLeft size={16} /> Quay lại
              </button>
            )}
            {currentStep === 1 && <div />}

            {currentStep < 3 && (
              <button type="button" className="btn btn-primary" onClick={handleNext}>
                Tiếp theo <ArrowRight size={16} />
              </button>
            )}

            {currentStep === 3 && (
              <button type="button" className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
                {loading ? (
                  <>
                    <RefreshCw size={16} className="spin" /> Đang tính toán AI...
                  </>
                ) : (
                  <>
                    <Send size={16} /> Chấm điểm AI ngay
                  </>
                )}
              </button>
            )}

            {currentStep === 4 && (
              <button type="button" className="btn btn-secondary" onClick={handleReset} style={{ margin: '0 auto' }}>
                <RefreshCw size={16} /> Nhập hồ sơ vay mới
              </button>
            )}
          </div>
        </div>
      </main>

      <footer className="footer">
        © 2026 DATN — Credit Risk & Loan Origination System | Powered by FastAPI + XGBoost AI Core
      </footer>
    </>
  );
};
