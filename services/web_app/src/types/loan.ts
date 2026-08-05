export interface LoanApplicationData {
  // Step 1: Personal & Demographics
  person_age: number;
  gender: 'MALE' | 'FEMALE';
  education_level: 'HIGH_SCHOOL' | 'BACHELOR' | 'MASTER' | 'DOCTORATE';
  marital_status: 'SINGLE' | 'MARRIED' | 'DIVORCED';
  
  // Step 2: Financial & Employment
  person_income: number;
  person_home_ownership: 'RENT' | 'OWN' | 'MORTGAGE' | 'OTHER';
  person_emp_length: number;
  employment_type: 'FULL_TIME' | 'PART_TIME' | 'SELF_EMPLOYED' | 'UNEMPLOYED';
  cb_person_default_on_file: 'Y' | 'N';
  cb_person_cred_hist_length: number;
  past_delinquencies: number;

  // Step 3: Loan Details
  loan_intent: 'PERSONAL' | 'EDUCATION' | 'MEDICAL' | 'VENTURE' | 'HOMEIMPROVEMENT' | 'DEBTCONSOLIDATION';
  loan_grade: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G';
  loan_amnt: number;
  loan_int_rate: number;
  loan_percent_income: number;
  loan_to_income_ratio: number;
  debt_to_income_ratio: number;
  credit_utilization_ratio: number;
}

export interface CreditRiskAssessment {
  pd_score: number;
  credit_score: number;
  risk_tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  decision: 'APPROVED' | 'MANUAL_REVIEW' | 'REJECTED';
}

export interface PredictApiResponse {
  success: boolean;
  task: string;
  application_summary: {
    income: number;
    loan_amount: number;
    intent: string;
  };
  credit_risk_assessment: CreditRiskAssessment;
}

export interface SaveEnrichedRecordPayload {
  application: LoanApplicationData;
  loan_status: 0 | 1;
  ml_pd_score: number;
  ml_credit_score: number;
  ml_decision: string;
}
