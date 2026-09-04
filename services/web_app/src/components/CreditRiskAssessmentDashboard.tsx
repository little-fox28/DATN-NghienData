import React from 'react';
import { useTranslation } from 'react-i18next';
import type { CreditRiskAssessment, RiskBasedPricingRecommendation } from '../types/loan';

export interface CreditRiskAssessmentDashboardProps {
  assessment: CreditRiskAssessment;
  requestedAmount?: number;
  requestedRate?: number;
  income?: number;
  intent?: string;
  applicationId?: string;
  rawFeatures?: Record<string, any>;
  onApproveProbingLimit?: () => void;
  onModifyTerms?: () => void;
  onReject?: () => void;
  isSaving?: boolean;
  isSaved?: boolean;
}

export const CreditRiskAssessmentDashboard: React.FC<CreditRiskAssessmentDashboardProps> = ({
  assessment,
  requestedAmount = 0,
  requestedRate,
  income = 0,
  intent,
  applicationId = 'N/A',
  rawFeatures,
  onApproveProbingLimit,
  onModifyTerms,
  onReject,
  isSaving = false,
  isSaved = false,
}) => {
  const { t } = useTranslation();

  const {
    pd_score = 0,
    credit_score = 0,
    risk_tier = 'UNKNOWN',
    decision = 'MANUAL_REVIEW',
    top_factors,
    contributions,
    pricing_recommendation,
  } = assessment || {};

  const pricing: RiskBasedPricingRecommendation = pricing_recommendation || {
    recommended_interest_rate: requestedRate || 0,
    base_rate: 0,
    risk_spread: 0,
    capital_discount: 0,
    intent_adjustment: 0,
    max_credit_limit: requestedAmount || 0,
    requested_amount: requestedAmount || 0,
    limit_status: decision === 'REJECTED' ? 'REJECTED' : 'WITHIN_LIMIT',
    loan_term_months: 36,
    monthly_payment_estimate: 0,
    total_interest_estimate: 0,
  };

  const maxLimit = pricing.max_credit_limit ?? 0;
  const reqAmount = pricing.requested_amount || requestedAmount || 0;

  // Dynamic limit calculation: Requested Amount vs ML Recommended Max Limit
  const limitPercent = maxLimit > 0 ? Math.min(Math.round((reqAmount / maxLimit) * 100), 100) : 0;
  const isWithinLimit = maxLimit > 0 ? reqAmount <= maxLimit : false;

  // Format real raw feature values dynamically from user inputs
  const formatRawValue = (featureKey: string): string => {
    const val = rawFeatures?.[featureKey] ?? (
      featureKey === 'person_income' ? income :
      featureKey === 'loan_amnt' ? requestedAmount :
      featureKey === 'loan_int_rate' ? requestedRate :
      featureKey === 'loan_intent' ? intent :
      undefined
    );

    if (val === undefined || val === null || val === '') {
      return '';
    }

    if (typeof val === 'number') {
      if (featureKey.includes('ratio') || featureKey.includes('percent')) {
        return `${(val > 1 ? val : val * 100).toFixed(1)}%`;
      }
      if (featureKey.includes('income') || featureKey.includes('amnt')) {
        return `$${val.toLocaleString()}`;
      }
      if (featureKey.includes('rate')) {
        return `${val.toFixed(2)}%`;
      }
      if (featureKey.includes('emp_length') || featureKey.includes('cred_hist')) {
        return `${val} ${t('common.years', 'năm')}`;
      }
      return String(val);
    }
    return String(val);
  };

  const getFeatureLabel = (featureKey: string): string => {
    const key = `riskDashboard.features.${featureKey}`;
    const translated = t(key);
    const baseName = translated !== key ? translated : featureKey.replace(/_/g, ' ');
    const rawVal = formatRawValue(featureKey);
    return rawVal ? `${baseName} (${rawVal})` : baseName;
  };

  // Extract positive/negative factors purely from real assessment payload
  const positiveFactors = top_factors?.positive_factors
    ? top_factors.positive_factors
    : contributions
    ? Object.entries(contributions)
        .filter(([_, pts]) => pts > 0)
        .sort(([_, a], [__, b]) => b - a)
        .slice(0, 3)
        .map(([feature, points]) => ({ feature, points }))
    : [];

  const negativeFactors = top_factors?.negative_factors
    ? top_factors.negative_factors
    : contributions
    ? Object.entries(contributions)
        .filter(([_, pts]) => pts < 0)
        .sort(([_, a], [__, b]) => a - b)
        .slice(0, 3)
        .map(([feature, points]) => ({ feature, points }))
    : [];

  const getDecisionStatusText = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return t('riskDashboard.decision.approved', 'HỒ SƠ ĐƯỢC PHÊ DUYỆT TỰ ĐỘNG');
      case 'APPROVED_CONDITIONAL':
        return t('riskDashboard.decision.approvedConditional', 'PHÊ DUYỆT CÓ ĐIỀU KIỆN (TĂNG LÃI SUẤT)');
      case 'MANUAL_REVIEW':
        return t('riskDashboard.decision.manualReview', 'CHUYỂN CÁN BỘ THẨM ĐỊNH THỦ CÔNG');
      case 'REJECTED':
        return t('riskDashboard.decision.rejected', 'HỒ SƠ BỊ TỪ CHỐI TỰ ĐỘNG');
      default:
        return status;
    }
  };

  const getDecisionStatusStyle = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'text-emerald-600 dark:text-emerald-400 font-semibold';
      case 'APPROVED_CONDITIONAL':
        return 'text-teal-600 dark:text-teal-400 font-semibold';
      case 'MANUAL_REVIEW':
        return 'text-amber-500 dark:text-amber-400 font-semibold';
      case 'REJECTED':
        return 'text-rose-500 dark:text-rose-400 font-semibold';
      default:
        return 'text-slate-700 dark:text-neutral-300 font-semibold';
    }
  };

  // Dynamic FICO score styling based on score brackets
  const getFicoScoreStyle = (score: number) => {
    if (score >= 740) return 'text-emerald-600 dark:text-emerald-400';
    if (score >= 670) return 'text-teal-600 dark:text-teal-400';
    if (score >= 580) return 'text-amber-500 dark:text-amber-400';
    return 'text-rose-500 dark:text-rose-400';
  };

  // Dynamic PD score styling based on default probability threshold
  const getPdScoreStyle = (pd: number) => {
    if (pd <= 0.02) return 'text-emerald-600 dark:text-emerald-400';
    if (pd <= 0.05) return 'text-teal-600 dark:text-teal-400';
    if (pd <= 0.10) return 'text-amber-500 dark:text-amber-400';
    return 'text-rose-500 dark:text-rose-400';
  };

  // Dynamic Risk Tier styling
  const getRiskTierStyle = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'LOW':
        return 'text-emerald-600 dark:text-emerald-400';
      case 'MEDIUM_LOW':
        return 'text-teal-600 dark:text-teal-400';
      case 'MEDIUM_HIGH':
        return 'text-amber-500 dark:text-amber-400';
      case 'HIGH':
      default:
        return 'text-rose-500 dark:text-rose-400';
    }
  };

  const getRiskTierText = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'HIGH':
        return t('riskDashboard.coreMetrics.tierHigh', 'Rủi ro Cao');
      case 'MEDIUM_HIGH':
        return t('riskDashboard.coreMetrics.tierMedHigh', 'Trung bình Cao');
      case 'MEDIUM_LOW':
        return t('riskDashboard.coreMetrics.tierMedLow', 'Trung bình Thấp');
      case 'LOW':
        return t('riskDashboard.coreMetrics.tierLow', 'Rủi ro Thấp');
      default:
        return tier;
    }
  };

  const getDerivedGrade = (score: number): string => {
    if (score >= 750) return 'A';
    if (score >= 700) return 'B';
    if (score >= 650) return 'C';
    if (score >= 600) return 'D';
    if (score >= 550) return 'E';
    if (score >= 500) return 'F';
    return 'G';
  };

  const currentGrade = assessment?.loan_grade || rawFeatures?.loan_grade || getDerivedGrade(credit_score);

  const getLoanGradeStyle = (grade: string) => {
    switch (String(grade).toUpperCase()) {
      case 'A':
        return 'text-emerald-600 dark:text-emerald-400';
      case 'B':
        return 'text-teal-600 dark:text-teal-400';
      case 'C':
        return 'text-amber-500 dark:text-amber-400';
      case 'D':
        return 'text-orange-500 dark:text-orange-400';
      case 'E':
      case 'F':
      case 'G':
      default:
        return 'text-rose-500 dark:text-rose-400';
    }
  };

  return (
    <div className="w-full space-y-4 text-slate-800 dark:text-gray-100 font-sans">
      {/* 1. Header / Status */}
      <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs flex items-center justify-between transition-colors">
        <div>
          <span className="text-xs uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium">
            {t('riskDashboard.header.applicationId', 'Mã Hồ sơ Vay')}
          </span>
          <div className="text-base font-semibold text-slate-900 dark:text-white mt-0.5">{applicationId}</div>
        </div>
        <div className="text-right">
          <span className="text-xs uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium block">
            {t('riskDashboard.header.decisionStatus', 'Trạng thái Quyết định')}
          </span>
          <span className={`text-sm mt-0.5 inline-block ${getDecisionStatusStyle(decision)}`}>
            {getDecisionStatusText(decision)}
          </span>
        </div>
      </div>

      {/* 2. Core Metrics (Grid of 4 cards with Dynamic Risk & Grade Coloring) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* FICO Score */}
        <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs transition-colors">
          <div className="text-sm text-gray-500 dark:text-gray-400">{t('riskDashboard.coreMetrics.ficoScore', 'Điểm Tín dụng FICO')}</div>
          <div className={`text-2xl font-semibold mt-1 ${getFicoScoreStyle(credit_score)}`}>{credit_score}</div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t('riskDashboard.coreMetrics.ficoScale', 'Thang đo chuẩn (300 - 850)')}</div>
        </div>

        {/* Loan Grade */}
        <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs transition-colors">
          <div className="text-sm text-gray-500 dark:text-gray-400">{t('riskDashboard.coreMetrics.loanGrade', 'Hạng Tín dụng')}</div>
          <div className={`text-2xl font-semibold mt-1 ${getLoanGradeStyle(currentGrade)}`}>
            {`Grade ${String(currentGrade).toUpperCase()}`}
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t('riskDashboard.coreMetrics.gradeScale', 'Phân hạng nội bộ (A - G)')}</div>
        </div>

        {/* Probability of Default (PD) */}
        <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs transition-colors">
          <div className="text-sm text-gray-500 dark:text-gray-400">{t('riskDashboard.coreMetrics.pdScore', 'Xác suất Vỡ nợ (PD)')}</div>
          <div className={`text-2xl font-semibold mt-1 ${getPdScoreStyle(pd_score)}`}>
            {(pd_score * 100).toFixed(2)}%
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t('riskDashboard.coreMetrics.pdThreshold', 'Ngưỡng cảnh báo: 5.00%')}</div>
        </div>

        {/* Risk Tier */}
        <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs transition-colors">
          <div className="text-sm text-gray-500 dark:text-gray-400">{t('riskDashboard.coreMetrics.riskTier', 'Phân hạng Rủi ro')}</div>
          <div className={`text-2xl font-semibold mt-1 ${getRiskTierStyle(risk_tier)}`}>{getRiskTierText(risk_tier)}</div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">{t('riskDashboard.coreMetrics.creditClassification', 'Phân loại Tín dụng')}</div>
        </div>
      </div>

      {/* 3. XAI Factors (Clean 2-Column List with raw data values and items-start alignment) */}
      <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs transition-colors">
        <div className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
          {t('riskDashboard.explainability.title', 'Giải thích Mô hình (Top Factors)')}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <div>
            <div className="text-xs uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium mb-2">
              {t('riskDashboard.explainability.positiveSignals', 'Tín hiệu Tích cực')}
            </div>
            <div className="divide-y divide-gray-100 dark:divide-[#262626]">
              {positiveFactors.length > 0 ? (
                positiveFactors.map((f, i) => (
                  <div key={i} className="py-2.5 flex justify-between items-center text-sm gap-2">
                    <span className="text-slate-700 dark:text-gray-200 font-normal">{getFeatureLabel(f.feature)}</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-medium shrink-0">
                      +{Number(f.points).toFixed(2)} {t('riskDashboard.explainability.pts', 'pts')}
                    </span>
                  </div>
                ))
              ) : (
                <div className="py-3 text-xs text-gray-400 dark:text-gray-500 italic">
                  {t('riskDashboard.explainability.emptyPositive', 'Không ghi nhận tín hiệu tích cực vượt trội')}
                </div>
              )}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium mb-2">
              {t('riskDashboard.explainability.negativeSignals', 'Tín hiệu Rủi ro')}
            </div>
            <div className="divide-y divide-gray-100 dark:divide-[#262626]">
              {negativeFactors.length > 0 ? (
                negativeFactors.map((f, i) => (
                  <div key={i} className="py-2.5 flex justify-between items-center text-sm gap-2">
                    <span className="text-slate-700 dark:text-gray-200 font-normal">{getFeatureLabel(f.feature)}</span>
                    <span className="text-rose-500 dark:text-rose-400 font-medium shrink-0">
                      {Number(f.points) > 0 ? `-${Number(f.points).toFixed(2)}` : Number(f.points).toFixed(2)} {t('riskDashboard.explainability.pts', 'pts')}
                    </span>
                  </div>
                ))
              ) : (
                <div className="py-3 text-xs text-gray-400 dark:text-gray-500 italic">
                  {t('riskDashboard.explainability.emptyNegative', 'Không ghi nhận yếu tố rủi ro bất thường')}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 4. Pricing & Limit Recommendation with Visible Track Progress Bar */}
      <div className="bg-white dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] rounded-lg p-4 shadow-xs transition-colors">
        <div className="text-sm font-semibold text-slate-900 dark:text-white mb-3">
          {t('riskDashboard.pricingAndLimit.title', 'Định giá Lãi suất & Đề xuất Hạn mức')}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1">
            <div className="flex justify-between border-b border-gray-100 dark:border-[#262626] py-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.aprLabel', 'LÃI SUẤT ĐỀ XUẤT (APR)')}</span>
              <span className="text-base font-semibold text-slate-900 dark:text-white">
                {Number(pricing.recommended_interest_rate).toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between border-b border-gray-100 dark:border-[#262626] py-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.baseRate', 'Lãi suất Cơ sở (Base)')}</span>
              <span className="text-slate-700 dark:text-gray-300 font-medium">{Number(pricing.base_rate).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between border-b border-gray-100 dark:border-[#262626] py-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.riskSpread', 'Biên độ Rủi ro (Risk Spread)')}</span>
              <span className="text-slate-700 dark:text-gray-300 font-medium">+{Number(pricing.risk_spread).toFixed(2)}%</span>
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between border-b border-gray-100 dark:border-[#262626] py-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.monthlyPayment', 'Ước tính Trả góp Hàng tháng')}</span>
              <span className="text-slate-900 dark:text-white font-semibold">
                ${Number(pricing.monthly_payment_estimate).toLocaleString(undefined, { minimumFractionDigits: 2 })} / {t('pricing.month', 'tháng')}
              </span>
            </div>
            <div className="flex justify-between border-b border-gray-100 dark:border-[#262626] py-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.totalInterest', 'Tổng Lãi Dự thu Cả kỳ')}</span>
              <span className="text-slate-700 dark:text-gray-300 font-medium">
                ${Number(pricing.total_interest_estimate).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between border-b border-gray-100 dark:border-[#262626] py-2 text-sm">
              <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.loanTerm', 'Kỳ hạn Vay')}</span>
              <span className="text-slate-700 dark:text-gray-300 font-medium">
                {pricing.loan_term_months || 36} {t('pricing.month', 'tháng')}
              </span>
            </div>
          </div>
        </div>

        {/* 5. Dynamic Limit Bar: Requested Amount vs ML Recommended Limit */}
        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-[#262626]">
          <div className="flex justify-between items-center text-sm mb-2">
            <span className="text-gray-500 dark:text-gray-400">{t('riskDashboard.pricingAndLimit.limitAllocation', 'Số tiền Yêu cầu / Hạn mức Khuyến nghị (ML)')}</span>
            <span className="font-semibold text-slate-900 dark:text-white">
              ${reqAmount.toLocaleString()} / ${maxLimit.toLocaleString()} ({limitPercent}%)
            </span>
          </div>
          {/* Progress track container with distinct dark background */}
          <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                isWithinLimit
                  ? 'bg-emerald-500 dark:bg-emerald-400'
                  : 'bg-amber-500 dark:bg-amber-400'
              }`}
              style={{ width: `${limitPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* 6. Action Workspace (Underwriter Decision Buttons) */}
      <div className="flex flex-wrap items-center justify-end gap-3 pt-3">
        <button
          type="button"
          onClick={onReject}
          className="px-4 py-2 text-sm font-medium rounded-lg border border-rose-300 dark:border-rose-900/60 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500/20 cursor-pointer"
        >
          {t('loanApplication.buttons.reject', 'Từ chối Hồ sơ')}
        </button>

        <button
          type="button"
          onClick={onModifyTerms}
          className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-700 text-slate-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/80 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500/20 cursor-pointer"
        >
          {t('loanApplication.buttons.modifyTerms', 'Điều chỉnh Điều khoản')}
        </button>

        <button
          type="button"
          onClick={onApproveProbingLimit}
          disabled={isSaving || isSaved}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors shadow-xs focus:outline-none flex items-center gap-2 ${
            isSaved
              ? 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 cursor-not-allowed'
              : decision === 'APPROVED' || decision === 'APPROVED_CONDITIONAL'
              ? 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-2 focus:ring-emerald-500/40 cursor-pointer disabled:opacity-60'
              : 'bg-amber-400 hover:bg-amber-500 text-slate-950 focus:ring-2 focus:ring-amber-500/40 cursor-pointer disabled:opacity-60'
          }`}
        >
          {isSaving ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{t('loanApplication.buttons.saving', 'Đang lưu hồ sơ...')}</span>
            </>
          ) : isSaved ? (
            <>
              <span>✓ {t('loanApplication.buttons.created', 'Đã tạo hồ sơ vay')}</span>
            </>
          ) : (
            decision === 'APPROVED' || decision === 'APPROVED_CONDITIONAL'
              ? t('loanApplication.buttons.approveDirect', 'Chấp thuận Phê duyệt Hạn mức')
              : t('loanApplication.buttons.approveLimit', 'Phê duyệt Hạn mức Thăm dò')
          )}
        </button>
      </div>
    </div>
  );
};
