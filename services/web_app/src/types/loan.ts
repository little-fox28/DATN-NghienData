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
  loan_term_months?: number;
  client_ID?: string;
  loan_percent_income: number;
  loan_to_income_ratio: number;
  debt_to_income_ratio: number;
  credit_utilization_ratio: number;
}

export interface RiskBasedPricingRecommendation {
  recommended_interest_rate: number;
  base_rate: number;
  risk_spread: number;
  capital_discount: number;
  intent_adjustment: number;
  max_credit_limit: number;
  requested_amount: number;
  limit_status: 'WITHIN_LIMIT' | 'EXCEEDS_RECOMMENDED_LIMIT' | 'REJECTED';
  loan_term_months?: number;
  monthly_payment_estimate?: number;
  total_interest_estimate?: number;
}

export interface CreditRiskAssessment {
  pd_score: number;
  credit_score: number;
  risk_tier: 'LOW' | 'MEDIUM_LOW' | 'MEDIUM_HIGH' | 'HIGH';
  decision: 'APPROVED' | 'APPROVED_CONDITIONAL' | 'MANUAL_REVIEW' | 'REJECTED';
  contributions?: Record<string, number>;
  top_factors?: {
    positive_factors: Array<{ feature: string; points: number }>;
    negative_factors: Array<{ feature: string; points: number }>;
  };
  pricing_recommendation?: RiskBasedPricingRecommendation;
}

export interface PredictApiResponse {
  success: boolean;
  task: string;
  client_id?: string;
  application_id?: string;
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
