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
  ml_risk_tier?: string;
  top_positive_factors?: Array<{ feature: string; points: number }>;
  top_negative_factors?: Array<{ feature: string; points: number }>;
  recommended_interest_rate?: number;
  max_credit_limit?: number;
  monthly_payment_estimate?: number;
  total_interest_estimate?: number;
}

export interface PortfolioKPIs {
  total_loan_volume: number;
  total_applications: number;
  overall_default_rate: number;
  avg_interest_rate: number;
  avg_annual_income: number;
  avg_lti: number;
  avg_dti: number;
  avg_utilization: number;
  avg_fico_score: number;
  pending_manual_reviews: number;
}

export interface RiskTierItem {
  tier: string;
  name: string;
  fico_range: string;
  pct: number;
  color: string;
  decision: string;
}

export interface GradeItem {
  grade: string;
  count: number;
  pct: number;
  volume: number;
  avg_rate: number;
  default_rate: number;
}

export interface IntentItem {
  intent: string;
  count: number;
  pct: number;
  volume: number;
  default_rate: number;
}

export interface TermItem {
  term_months: number;
  count: number;
  pct: number;
  volume: number;
  default_rate: number;
  woe_points: number;
}

export interface HomeOwnershipItem {
  ownership: string;
  count: number;
  pct: number;
  volume: number;
  default_rate: number;
}

export interface PortfolioSummaryResponse {
  success: boolean;
  kpis: PortfolioKPIs;
  risk_tiers: RiskTierItem[];
  grades: GradeItem[];
  intents: IntentItem[];
  terms: TermItem[];
  home_ownership: HomeOwnershipItem[];
}

export interface EnrichedRecordItem {
  application_id?: string;
  client_ID?: string;
  display_client_ID?: string;
  person_age: number;
  person_income: number;
  person_home_ownership: string;
  person_emp_length: number;
  loan_intent: string;
  loan_grade: string;
  loan_amnt: number;
  loan_int_rate: number;
  loan_term_months?: number;
  loan_status: string | number;
  loan_percent_income: number;
  loan_to_income_ratio: number;
  debt_to_income_ratio: number;
  cb_person_default_on_file: string;
  cb_person_cred_hist_length: number;
  gender?: string;
  marital_status?: string;
  education_level?: string;
  employment_type?: string;
  ml_pd_score?: number;
  ml_credit_score?: number;
  ml_decision?: string;
  ml_risk_tier?: string;
  top_positive_factors?: Array<{ feature: string; points: number }> | string;
  top_negative_factors?: Array<{ feature: string; points: number }> | string;
  recommended_interest_rate?: number;
  max_credit_limit?: number;
  monthly_payment_estimate?: number;
  total_interest_estimate?: number;
  created_at?: string;
}

