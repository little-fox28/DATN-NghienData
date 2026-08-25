import { Button, Form, InputNumber, Modal, Popconfirm, Select, Tag, Tooltip } from 'antd';
import {
  CheckCircle,
  DollarSign,
  Edit3,
  HelpCircle,
  ShieldCheck,
  Trash2,
  TrendingDown,
  TrendingUp,
  User,
  XCircle,
} from 'lucide-react';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnrichedRecordItem } from '../../types/loan';

export interface CaseInspectionModalProps {
  open: boolean;
  onClose: () => void;
  record: EnrichedRecordItem | null;
  onApprove?: (record: EnrichedRecordItem) => void;
  onReject?: (record: EnrichedRecordItem) => void;
  onDelete?: (record: EnrichedRecordItem) => void;
  onModify?: (clientId: string, updates: Partial<EnrichedRecordItem>) => void;
}

export const CaseInspectionModal: React.FC<CaseInspectionModalProps> = ({
  open,
  onClose,
  record,
  onApprove,
  onReject,
  onDelete,
  onModify,
}) => {
  const { t } = useTranslation();
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [form] = Form.useForm();

  // Watch form values for real-time recalculation in the edit modal
  const formLoanAmnt = Form.useWatch('loan_amnt', form);
  const formTermMonths = Form.useWatch('loan_term_months', form);
  const formRecommendedApr = Form.useWatch('recommended_interest_rate', form);

  if (!record) return null;

  const ficoScore = Number(record.ml_credit_score) > 0 ? Number(record.ml_credit_score) : 670;
  const rawPd = Number(record.ml_pd_score) || 0.045;
  const pdScore = rawPd > 1 ? rawPd / 100 : rawPd;
  const decision = record.ml_decision || (ficoScore >= 740 ? 'APPROVED' : ficoScore >= 670 ? 'APPROVED_CONDITIONAL' : ficoScore >= 580 ? 'MANUAL_REVIEW' : 'REJECTED');
  
  const getFicoColor = (score: number) => {
    if (score >= 740) return 'text-emerald-600 dark:text-emerald-400';
    if (score >= 670) return 'text-teal-600 dark:text-teal-400';
    if (score >= 580) return 'text-amber-500 dark:text-amber-400';
    return 'text-rose-500 dark:text-rose-400';
  };

  const getDecisionBadge = (dec: string) => {
    switch (dec) {
      case 'APPROVED':
        return <Tag color="success" className="font-bold">{t('riskDashboard.decision.approved', 'APPROVED')}</Tag>;
      case 'APPROVED_CONDITIONAL':
        return <Tag color="cyan" className="font-bold">{t('riskDashboard.decision.approvedConditional', 'APPROVED_CONDITIONAL')}</Tag>;
      case 'MANUAL_REVIEW':
        return <Tag color="warning" className="font-bold">{t('riskDashboard.decision.manualReview', 'MANUAL_REVIEW')}</Tag>;
      case 'REJECTED':
        return <Tag color="error" className="font-bold">{t('riskDashboard.decision.rejected', 'REJECTED')}</Tag>;
      default:
        return <Tag color="default" className="font-bold">{dec}</Tag>;
    }
  };

  // Extract positive and negative XAI factors
  let positiveFactors: Array<{ feature: string; points: number }> = [];
  let negativeFactors: Array<{ feature: string; points: number }> = [];

  try {
    if (Array.isArray(record.top_positive_factors)) {
      positiveFactors = record.top_positive_factors;
    } else if (typeof record.top_positive_factors === 'string' && record.top_positive_factors.startsWith('[')) {
      positiveFactors = JSON.parse(record.top_positive_factors);
    }
  } catch (e) {
    positiveFactors = [];
  }

  try {
    if (Array.isArray(record.top_negative_factors)) {
      negativeFactors = record.top_negative_factors;
    } else if (typeof record.top_negative_factors === 'string' && record.top_negative_factors.startsWith('[')) {
      negativeFactors = JSON.parse(record.top_negative_factors);
    }
  } catch (e) {
    negativeFactors = [];
  }

  // Fallbacks if not present in record
  if (positiveFactors.length === 0) {
    positiveFactors = [
      { feature: 'debt_to_income_ratio', points: 4.51 },
      { feature: 'person_income', points: 2.88 },
      { feature: 'loan_to_income_ratio', points: 2.50 },
    ];
  }

  if (negativeFactors.length === 0) {
    negativeFactors = [
      { feature: 'person_home_ownership', points: -2.57 },
    ];
  }

  const getFeatureLabel = (featureKey: string): string => {
    const key = `riskDashboard.features.${featureKey}`;
    const translated = t(key);
    const baseName = translated !== key ? translated : featureKey.replace(/_/g, ' ');
    if (featureKey === 'person_income') return `${baseName} ($${Number(record.person_income || 0).toLocaleString()})`;
    if (featureKey === 'person_home_ownership') return `${baseName} (${record.person_home_ownership || 'RENT'})`;
    if (featureKey === 'loan_to_income_ratio' || featureKey === 'debt_to_income_ratio') {
      const val = Number(record[featureKey as keyof EnrichedRecordItem] || 0.15);
      return `${baseName} (${(val > 1 ? val : val * 100).toFixed(1)}%)`;
    }
    return baseName;
  };

  const requestedAmnt = Number(record.loan_amnt || 10000);
  const maxLimit = Number(record.max_credit_limit || requestedAmnt * 1.5);
  const recommendedApr = Number(record.recommended_interest_rate || record.loan_int_rate || 9.0);
  const monthlyPayment = Number(record.monthly_payment_estimate || (requestedAmnt / (record.loan_term_months || 36)) * 1.15);
  const totalInterest = Number(record.total_interest_estimate || requestedAmnt * (recommendedApr / 100) * ((record.loan_term_months || 36) / 12));
  const limitPct = maxLimit > 0 ? Math.min(Math.round((requestedAmnt / maxLimit) * 100), 100) : 50;

  const handleOpenEdit = () => {
    form.setFieldsValue({
      loan_amnt: requestedAmnt,
      loan_term_months: record.loan_term_months || 36,
      recommended_interest_rate: recommendedApr,
      max_credit_limit: maxLimit,
      loan_grade: record.loan_grade || 'B',
      ml_decision: record.ml_decision || 'MANUAL_REVIEW',
    });
    setIsEditModalOpen(true);
  };

  // Helper formula to compute PMT
  const calculatePMT = (principal: number, annualRate: number, months: number) => {
    if (!principal || !months) return 0;
    if (!annualRate) return principal / months;
    const r = annualRate / 100 / 12;
    const pmt = (principal * r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
    return Math.round(pmt * 100) / 100;
  };

  const currentEditPmt = calculatePMT(
    Number(formLoanAmnt || requestedAmnt),
    Number(formRecommendedApr || recommendedApr),
    Number(formTermMonths || record.loan_term_months || 36)
  );
  const currentEditTotalInterest = Math.round(
    (currentEditPmt * Number(formTermMonths || record.loan_term_months || 36) - Number(formLoanAmnt || requestedAmnt)) * 100
  ) / 100;

  const handleSaveEdit = async () => {
    try {
      const values = await form.validateFields();
      const pmt = calculatePMT(values.loan_amnt, values.recommended_interest_rate, values.loan_term_months);
      const interestEst = Math.round((pmt * values.loan_term_months - values.loan_amnt) * 100) / 100;

      if (onModify && record.client_ID) {
        onModify(record.client_ID, {
          ...values,
          loan_int_rate: values.recommended_interest_rate,
          monthly_payment_estimate: pmt,
          total_interest_estimate: interestEst > 0 ? interestEst : 0,
          loan_status: values.ml_decision === 'APPROVED' ? 0 : (values.ml_decision === 'REJECTED' ? 1 : -1),
        });
      }
      setIsEditModalOpen(false);
    } catch (err) {
      console.error('Validation failed:', err);
    }
  };

  return (
    <>
      <Modal
        title={
          <div className="flex items-center justify-between pr-8">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-slate-900 dark:text-white text-base">
                {record.application_id || record.client_ID || 'APP-2026-CASE'}
              </span>
              {getDecisionBadge(decision)}
            </div>
            <span className="text-xs text-gray-400 font-mono">
              Client ID: {record.client_ID}
            </span>
          </div>
        }
        open={open}
        onCancel={onClose}
        width={840}
        footer={
          <div className="flex items-center justify-between pt-2">
            <div>
              {onDelete && (
                <Popconfirm
                  title={t('underwriting.notices.confirmDeleteTitle', 'Xác nhận xóa hồ sơ này khỏi hệ thống?')}
                  onConfirm={() => {
                    onDelete(record);
                    onClose();
                  }}
                  okText={t('underwriting.notices.deleteOk', 'Xóa')}
                  cancelText={t('underwriting.notices.deleteCancel', 'Hủy')}
                  okButtonProps={{ danger: true }}
                >
                  <Button danger icon={<Trash2 className="w-4 h-4" />}>
                    {t('underwriting.notices.deleteTooltip', 'Xóa hồ sơ')}
                  </Button>
                </Popconfirm>
              )}
            </div>

            <div className="flex items-center gap-2.5">
              <Button
                className="border-indigo-400 text-indigo-600 dark:text-indigo-400 hover:border-indigo-500 font-medium flex items-center gap-1.5"
                icon={<Edit3 className="w-4 h-4" />}
                onClick={handleOpenEdit}
              >
                {t('underwriting.drawer.modifyTerms', 'Điều Chỉnh Định Giá & Hạn Mức')}
              </Button>
              <Button
                danger
                icon={<XCircle className="w-4 h-4" />}
                onClick={() => {
                  if (onReject) onReject(record);
                  onClose();
                }}
              >
                {t('underwriting.drawer.reject', 'Từ Chối')}
              </Button>
              <Button
                type="primary"
                className="bg-emerald-600 hover:bg-emerald-500 border-none font-semibold"
                icon={<CheckCircle className="w-4 h-4" />}
                onClick={() => {
                  if (onApprove) onApprove(record);
                  onClose();
                }}
              >
                {t('underwriting.drawer.approveLimit', 'Phê Duyệt Hạn Mức')}
              </Button>
            </div>
          </div>
        }
        className="dark:bg-[#141414]"
      >
        <div className="space-y-4 text-slate-800 dark:text-gray-100 py-2">
          {/* 1. Core Risk Gauges & Metrics */}
          <div className="grid grid-cols-2 gap-3 p-4 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-200 dark:border-[#2a2a2a]">
            <div>
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                {t('underwriting.drawer.ficoScore', 'Điểm Tín Dụng (FICO Score)')}
              </span>
              <div className={`text-3xl font-bold font-mono tracking-tight mt-1 ${getFicoColor(ficoScore)}`}>
                {ficoScore}
                <span className="text-xs font-normal text-gray-400 dark:text-gray-500 ml-1.5">/ 850</span>
              </div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                {ficoScore >= 740
                  ? t('underwriting.drawer.tierPrime', 'Hạng Tín Dụng Prime')
                  : ficoScore >= 670
                  ? t('underwriting.drawer.tierStandard', 'Hạng Tiêu Chuẩn')
                  : ficoScore >= 580
                  ? t('underwriting.drawer.tierBorderline', 'Vùng đệm Thẩm định')
                  : t('underwriting.drawer.tierSubprime', 'Hồ sơ Dưới chuẩn')}
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                {t('underwriting.drawer.pdScore', 'Xác Suất Vỡ Nợ (PD)')}
              </span>
              <div className={`text-3xl font-bold font-mono tracking-tight mt-1 ${pdScore <= 0.05 ? 'text-emerald-600 dark:text-emerald-400' : pdScore <= 0.10 ? 'text-amber-500 dark:text-amber-400' : 'text-rose-500 dark:text-rose-400'}`}>
                {(pdScore * 100).toFixed(2)}%
              </div>
              <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                {t('underwriting.drawer.pdThreshold', 'Ngưỡng cảnh báo: 5.00%')}
              </div>
            </div>
          </div>

          {/* 2. Applicant & Loan Summary */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5" /> {t('underwriting.drawer.applicantSummary', 'Thông tin Người vay & Khoản vay')}
              </h4>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 block text-[11px]">{t('underwriting.drawer.income', 'Thu nhập Hàng năm:')}</span>
                <strong className="text-slate-900 dark:text-white font-mono text-sm">
                  ${Number(record.person_income || 0).toLocaleString()}
                </strong>
              </div>

              <div className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 block text-[11px]">{t('underwriting.drawer.amount', 'Số tiền Đề xuất Vay:')}</span>
                <strong className="text-slate-900 dark:text-white font-mono text-sm">
                  ${Number(record.loan_amnt || 0).toLocaleString()}
                </strong>
              </div>

              <div className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 block text-[11px]">{t('underwriting.drawer.intent', 'Mục đích Vay:')}</span>
                <strong className="text-slate-900 dark:text-white">{record.loan_intent || 'PERSONAL'}</strong>
              </div>

              <div className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 block text-[11px]">{t('underwriting.drawer.term', 'Kỳ hạn Vay (Loan Term):')}</span>
                <strong className="text-slate-900 dark:text-white font-mono">
                  {record.loan_term_months || 36} {t('pricing.month', 'tháng')}
                </strong>
              </div>

              <div className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 block text-[11px]">{t('underwriting.drawer.ownership', 'Sở hữu Nhà:')}</span>
                <strong className="text-slate-900 dark:text-white">{record.person_home_ownership || 'RENT'}</strong>
              </div>

              <div className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 block text-[11px]">{t('underwriting.drawer.empLength', 'Thâm niên Công tác:')}</span>
                <strong className="text-slate-900 dark:text-white font-mono">{record.person_emp_length || 0} {t('pricing.year', 'năm')}</strong>
              </div>
            </div>
          </div>

          {/* 3. Explainability (XAI) Signals */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> {t('underwriting.drawer.xaiTitle', 'Giải Thích Đóng Góp Điểm WoE (XAI)')}
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {/* Positive Factors */}
              <div className="p-2.5 rounded-lg border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/30 text-xs">
                <div className="flex items-center justify-between font-semibold text-emerald-800 dark:text-emerald-300 mb-1.5">
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-600" /> {t('underwriting.drawer.positiveSignals', 'Tín hiệu Tích cực')}
                  </span>
                </div>
                <div className="space-y-1">
                  {positiveFactors.map((f, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-emerald-900 dark:text-emerald-300 font-medium">{getFeatureLabel(f.feature)}</span>
                      <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                        +{Number(f.points).toFixed(2)} điểm
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Negative Factors */}
              <div className="p-2.5 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/30 text-xs">
                <div className="flex items-center justify-between font-semibold text-rose-800 dark:text-rose-300 mb-1.5">
                  <span className="flex items-center gap-1">
                    <TrendingDown className="w-3.5 h-3.5 text-rose-600" /> {t('underwriting.drawer.negativeSignals', 'Tín hiệu Cần lưu ý')}
                  </span>
                </div>
                <div className="space-y-1">
                  {negativeFactors.map((f, idx) => (
                    <div key={idx} className="flex justify-between items-center text-xs">
                      <span className="text-rose-900 dark:text-rose-300 font-medium">{getFeatureLabel(f.feature)}</span>
                      <span className="font-mono text-rose-600 dark:text-rose-400 font-bold">
                        {Number(f.points) > 0 ? `-${Number(f.points).toFixed(2)}` : Number(f.points).toFixed(2)} điểm
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 4. Editable Pricing & Limit Recommendation Section (AI Recommendation with Human Override) */}
          <div className="p-3.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-200 dark:border-[#2a2a2a] text-xs">
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-indigo-500" />
                <h4 className="font-bold uppercase tracking-wider text-slate-900 dark:text-white text-xs">
                  {t('riskDashboard.pricingAndLimit.title', 'Định giá Lãi suất & Đề xuất Hạn mức')}
                </h4>
                <Tooltip title="Các chỉ số dưới đây do AI đề xuất. Bạn có thể nhấn 'Chỉnh sửa' để ghi đè lãi suất, hạn mức và kỳ hạn phê duyệt.">
                  <HelpCircle className="w-3.5 h-3.5 text-gray-400 cursor-pointer" />
                </Tooltip>
              </div>

              <Button
                size="small"
                type="link"
                icon={<Edit3 className="w-3 h-3" />}
                className="text-xs text-indigo-600 dark:text-indigo-400 p-0 font-medium flex items-center gap-1"
                onClick={handleOpenEdit}
              >
                Chỉnh sửa gợi ý AI
              </Button>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-2.5">
              <div className="p-2 rounded-md bg-white dark:bg-[#141414] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 text-[11px] block">{t('riskDashboard.pricingAndLimit.aprLabel', 'Lãi suất Phê duyệt (APR):')}</span>
                <div className="font-bold font-mono text-slate-900 dark:text-white text-base mt-0.5">
                  {recommendedApr.toFixed(2)}%
                </div>
              </div>
              <div className="p-2 rounded-md bg-white dark:bg-[#141414] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 text-[11px] block">{t('riskDashboard.pricingAndLimit.monthlyPayment', 'Ước tính Trả góp:')}</span>
                <div className="font-bold font-mono text-slate-900 dark:text-white text-base mt-0.5">
                  ${monthlyPayment.toFixed(2)} / {t('pricing.month', 'tháng')}
                </div>
              </div>
              <div className="p-2 rounded-md bg-white dark:bg-[#141414] border border-gray-100 dark:border-[#262626]">
                <span className="text-gray-400 dark:text-gray-500 text-[11px] block">{t('riskDashboard.pricingAndLimit.totalInterest', 'Tổng Lãi Dự thu:')}</span>
                <div className="font-bold font-mono text-slate-900 dark:text-white text-base mt-0.5">
                  ${totalInterest.toFixed(2)}
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 dark:border-[#262626] pt-2.5">
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="text-gray-500 dark:text-gray-400 font-medium">
                  {t('riskDashboard.pricingAndLimit.limitAllocation', 'Hạn mức Cho vay Thực tế / Hạn mức Tối đa:')}
                </span>
                <span className="font-bold font-mono text-slate-900 dark:text-white">
                  ${requestedAmnt.toLocaleString()} / ${maxLimit.toLocaleString()} ({limitPct}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 transition-all duration-300"
                  style={{ width: `${limitPct}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </Modal>

      {/* Sub-modal: Interactive AI Pricing & Limit Override Form */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <Edit3 className="w-4 h-4 text-indigo-500" />
            <span>Ghi đè Định giá & Hạn mức Khoản vay ({record.client_ID})</span>
          </div>
        }
        open={isEditModalOpen}
        onOk={handleSaveEdit}
        onCancel={() => setIsEditModalOpen(false)}
        okText={t('underwriting.modal.save', 'Lưu thay đổi')}
        cancelText={t('underwriting.modal.cancel', 'Hủy')}
        width={560}
      >
        <Form form={form} layout="vertical" className="mt-4">
          <div className="p-3 bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/60 rounded-lg text-xs text-indigo-700 dark:text-indigo-300 mb-4">
            💡 <strong>Quyền hạn Thẩm định viên:</strong> Bạn có thể tùy chỉnh lãi suất, hạn mức và số tiền cho vay phù hợp với hồ sơ thực tế thay vì hoàn toàn phụ thuộc vào gợi ý AI.
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Form.Item
              name="loan_amnt"
              label="Số tiền cho vay ($)"
              rules={[{ required: true, message: t('underwriting.modal.requireAmount', 'Vui lòng nhập số tiền vay') }]}
            >
              <InputNumber className="w-full" min={500} max={100000} step={500} formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => Number(value!.replace(/\$\s?|(,*)/g, '')) as any} />
            </Form.Item>

            <Form.Item
              name="max_credit_limit"
              label="Hạn mức tối đa được cấp ($)"
              rules={[{ required: true, message: 'Vui lòng nhập hạn mức tối đa' }]}
            >
              <InputNumber className="w-full" min={500} max={200000} step={500} formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => Number(value!.replace(/\$\s?|(,*)/g, '')) as any} />
            </Form.Item>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Form.Item
              name="recommended_interest_rate"
              label="Lãi suất phê duyệt APR (%)"
              rules={[{ required: true, message: t('underwriting.modal.requireRate', 'Vui lòng nhập lãi suất') }]}
            >
              <InputNumber className="w-full" min={1} max={35} step={0.1} />
            </Form.Item>

            <Form.Item
              name="loan_term_months"
              label={t('underwriting.modal.loanTerm', 'Kỳ hạn vay (Tháng)')}
              rules={[{ required: true, message: t('underwriting.modal.requireTerm', 'Vui lòng chọn kỳ hạn vay') }]}
            >
              <Select
                options={[
                  { value: 12, label: `12 ${t('pricing.month', 'tháng (1 năm)')}` },
                  { value: 24, label: `24 ${t('pricing.month', 'tháng (2 năm)')}` },
                  { value: 36, label: `36 ${t('pricing.month', 'tháng (3 năm)')}` },
                  { value: 48, label: `48 ${t('pricing.month', 'tháng (4 năm)')}` },
                  { value: 60, label: `60 ${t('pricing.month', 'tháng (5 năm)')}` },
                ]}
              />
            </Form.Item>
          </div>

          {/* Real-time calculated estimates based on current form inputs */}
          <div className="p-3 bg-gray-50 dark:bg-[#1f1f1f] rounded-lg border border-gray-200 dark:border-[#2a2a2a] text-xs space-y-1 mb-4">
            <div className="flex justify-between font-medium">
              <span className="text-gray-500">Trả góp hàng tháng tự động tính (PMT):</span>
              <span className="text-slate-900 dark:text-white font-mono font-bold">${currentEditPmt.toFixed(2)} / tháng</span>
            </div>
            <div className="flex justify-between font-medium">
              <span className="text-gray-500">Tổng tiền lãi dự thu cả kỳ:</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-mono font-bold">${currentEditTotalInterest > 0 ? currentEditTotalInterest.toFixed(2) : '0.00'}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Form.Item
              name="loan_grade"
              label={t('underwriting.modal.loanGrade', 'Hạng Khoản vay (Grade A-G)')}
              rules={[{ required: true, message: t('underwriting.modal.requireGrade', 'Vui lòng chọn hạng khoản vay') }]}
            >
              <Select
                options={[
                  { value: 'A', label: 'Grade A (VIP Prime)' },
                  { value: 'B', label: 'Grade B (Standard)' },
                  { value: 'C', label: 'Grade C (Near Prime)' },
                  { value: 'D', label: 'Grade D (Borderline)' },
                  { value: 'E', label: 'Grade E (Subprime)' },
                  { value: 'F', label: 'Grade F' },
                  { value: 'G', label: 'Grade G (High Risk)' },
                ]}
              />
            </Form.Item>

            <Form.Item
              name="ml_decision"
              label={t('underwriting.modal.decision', 'Quyết định Thẩm định viên')}
              rules={[{ required: true }]}
            >
              <Select
                options={[
                  { value: 'APPROVED', label: t('underwriting.filter.decisionApproved', 'APPROVED (Phê duyệt)') },
                  { value: 'APPROVED_CONDITIONAL', label: t('underwriting.filter.decisionConditional', 'APPROVED CONDITIONAL (Có điều kiện)') },
                  { value: 'MANUAL_REVIEW', label: t('underwriting.filter.decisionManual', 'MANUAL REVIEW (Cần thẩm định)') },
                  { value: 'REJECTED', label: t('underwriting.filter.decisionRejected', 'REJECTED (Từ chối)') },
                ]}
              />
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </>
  );
};

export const CaseInspectionDrawer = CaseInspectionModal;
