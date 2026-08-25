import { CheckCircleOutlined, DatabaseOutlined, FileTextOutlined, LeftOutlined, ReloadOutlined, RightOutlined, SendOutlined, UserOutlined, WalletOutlined } from '@ant-design/icons';
import { App as AntApp, Button, Card, Col, Form, InputNumber, Row, Select, Steps, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { predictCreditRisk, saveEnrichedRecord } from '../api/client';
import { CreditRiskAssessmentDashboard } from '../components/CreditRiskAssessmentDashboard';
import type { LoanApplicationData, PredictApiResponse } from '../types/loan';

const { Title, Text } = Typography;
const { Option } = Select;

const initialFormData: LoanApplicationData = {
  person_age: 28,
  gender: 'MALE',
  education_level: 'BACHELOR',
  marital_status: 'SINGLE',
  person_income: 65000,
  person_home_ownership: 'RENT',
  person_emp_length: 4.0,
  employment_type: 'FULL_TIME',
  cb_person_default_on_file: 'N',
  cb_person_cred_hist_length: 3,
  past_delinquencies: 0,
  loan_intent: 'PERSONAL',
  loan_grade: 'B',
  loan_amnt: 10000,
  loan_int_rate: 11.14,
  loan_term_months: 36,
  loan_percent_income: 0.15,
  loan_to_income_ratio: 0.15,
  debt_to_income_ratio: 0.12,
  credit_utilization_ratio: 0.35,
};

export const LoanApplicationPage: React.FC = () => {
  const { t } = useTranslation();
  const { message, notification } = AntApp.useApp();
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [form] = Form.useForm<LoanApplicationData>();
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [result, setResult] = useState<PredictApiResponse | null>(null);
  const [savedClientId, setSavedClientId] = useState<string | null>(null);

  useEffect(() => {
    form.setFieldsValue(initialFormData);
  }, [form]);

  const steps = [
    { title: t('loanApplication.steps.demographics'), icon: <UserOutlined /> },
    { title: t('loanApplication.steps.financial'), icon: <WalletOutlined /> },
    { title: t('loanApplication.steps.intent'), icon: <FileTextOutlined /> },
    { title: t('loanApplication.steps.result'), icon: <CheckCircleOutlined /> },
  ];

  const handleNext = async () => {
    try {
      await form.validateFields();
      setCurrentStep(prev => Math.min(prev + 1, 3));
    } catch (err: any) {
      if (err.errorFields) {
        message.warning(t('loanApplication.errors.invalidInput'));
      }
    }
  };

  const handlePrev = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const person_income = values.person_income || 0;
      const loan_amnt = values.loan_amnt || 0;

      const updatedData: LoanApplicationData = {
        ...initialFormData,
        ...values,
        loan_percent_income: person_income > 0 ? Number((loan_amnt / person_income).toFixed(4)) : 0,
        loan_to_income_ratio: person_income > 0 ? Number((loan_amnt / person_income).toFixed(4)) : 0,
        debt_to_income_ratio: values.debt_to_income_ratio ?? 0.12,
      };

      const apiResult = await predictCreditRisk(updatedData, 'credit_risk');
      setResult(apiResult);
      setCurrentStep(3);
      message.success(t('loanApplication.messages.success'));
    } catch (err: any) {
      console.error(err);
      if (!err.errorFields) {
        let errorMsg = err?.response?.data?.detail;

        // Handle FastAPI validation array response to prevent React crash (White page)
        if (Array.isArray(errorMsg)) {
          errorMsg = errorMsg.map((e: any) => `${e.loc?.join(' -> ')}: ${e.msg}`).join('; ');
        } else if (typeof errorMsg === 'object' && errorMsg !== null) {
          errorMsg = JSON.stringify(errorMsg);
        } else if (!errorMsg) {
          errorMsg = t('loanApplication.errors.serverError');
        }

        notification.error({
          message: t('loanApplication.errors.systemError'),
          description: errorMsg as string,
          placement: 'topRight',
        });
      } else {
        message.warning(t('loanApplication.errors.invalidInput'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.setFieldsValue(initialFormData);
    setResult(null);
    setSavedClientId(null);
    setCurrentStep(0);
  };

  const handleSaveToDB = async () => {
    if (!result) return;
    try {
      setSaving(true);
      const values = form.getFieldsValue();
      const person_income = values.person_income || 0;
      const loan_amnt = values.loan_amnt || 0;
      const formData = {
        ...initialFormData,
        ...values,
        loan_percent_income: person_income > 0 ? Number((loan_amnt / person_income).toFixed(2)) : 0,
        loan_to_income_ratio: person_income > 0 ? Number((loan_amnt / person_income).toFixed(2)) : 0,
      };

      const resp = await saveEnrichedRecord({
        application: formData,
        loan_status: -1 as unknown as 0 | 1, // Status will be labeled later in data view
        ml_pd_score: result.credit_risk_assessment.pd_score,
        ml_credit_score: result.credit_risk_assessment.credit_score,
        ml_decision: result.credit_risk_assessment.decision,
        ml_risk_tier: result.credit_risk_assessment.risk_tier,
        top_positive_factors: result.credit_risk_assessment.top_factors?.positive_factors,
        top_negative_factors: result.credit_risk_assessment.top_factors?.negative_factors,
        recommended_interest_rate: result.credit_risk_assessment.pricing_recommendation?.recommended_interest_rate,
        max_credit_limit: result.credit_risk_assessment.pricing_recommendation?.max_credit_limit,
        monthly_payment_estimate: result.credit_risk_assessment.pricing_recommendation?.monthly_payment_estimate,
        total_interest_estimate: result.credit_risk_assessment.pricing_recommendation?.total_interest_estimate,
      });

      setSavedClientId(resp.client_ID);
      message.success(`${t('loanApplication.buttons.created')}`);
    } catch (err: any) {
      console.error(err);
      notification.error({
        message: t('loanApplication.buttons.errorSaveToDb'),
        description: err?.response?.data?.detail || 'Không thể lưu hồ sơ vào cơ sở dữ liệu.',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <Steps current={currentStep} items={steps} style={{ marginBottom: 40 }} />

      <Card bordered={false} className="form-container-card">
        <Form form={form} layout="vertical" disabled={loading}>
          {/* STEP 0: Personal Demographics */}
          <div style={{ display: currentStep === 0 ? 'block' : 'none' }}>
            <Title level={4}>{t('loanApplication.step1.title')}</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
              {t('loanApplication.step1.description')}
            </Text>

            <Row gutter={24}>
              <Col xs={24} md={12}>
                <Form.Item name="person_age" label={t('loanApplication.step1.age')} rules={[{ required: true, message: t('loanApplication.errors.requireAge') }]}>
                  <InputNumber style={{ width: '100%' }} min={18} max={85} size="large" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="gender" label={t('loanApplication.step1.gender')} rules={[{ required: true, message: t('loanApplication.errors.requireGender') }]}>
                  <Select size="large">
                    <Option value="MALE">{t('loanApplication.step1.male')}</Option>
                    <Option value="FEMALE">{t('loanApplication.step1.female')}</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="education_level" label={t('loanApplication.step1.education')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value="HIGH_SCHOOL">{t('loanApplication.step1.highSchool')}</Option>
                    <Option value="BACHELOR">{t('loanApplication.step1.bachelor')}</Option>
                    <Option value="MASTER">{t('loanApplication.step1.master')}</Option>
                    <Option value="DOCTORATE">{t('loanApplication.step1.doctorate')}</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="marital_status" label={t('loanApplication.step1.maritalStatus')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value="SINGLE">{t('loanApplication.step1.single')}</Option>
                    <Option value="MARRIED">{t('loanApplication.step1.married')}</Option>
                    <Option value="DIVORCED">{t('loanApplication.step1.divorced')}</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </div>

          {/* STEP 1: Financial & Employment */}
          <div style={{ display: currentStep === 1 ? 'block' : 'none' }}>
            <Title level={4}>{t('loanApplication.step2.title')}</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
              {t('loanApplication.step2.description')}
            </Text>

            <Row gutter={24}>
              <Col xs={24} md={12}>
                <Form.Item name="person_income" label={t('loanApplication.step2.income')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <InputNumber style={{ width: '100%' }} min={0} size="large" formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => Number(value!.replace(/\$\s?|(,*)/g, '')) as any} />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="person_home_ownership" label={t('loanApplication.step2.homeOwnership')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value="RENT">{t('loanApplication.step2.rent')}</Option>
                    <Option value="OWN">{t('loanApplication.step2.own')}</Option>
                    <Option value="MORTGAGE">{t('loanApplication.step2.mortgage')}</Option>
                    <Option value="OTHER">{t('loanApplication.step2.other')}</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="person_emp_length" label={t('loanApplication.step2.empLength')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <InputNumber style={{ width: '100%' }} min={0} step={0.5} size="large" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="cb_person_default_on_file" label={t('loanApplication.step2.defaultHist')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value="N">{t('loanApplication.step2.no')}</Option>
                    <Option value="Y">{t('loanApplication.step2.yes')}</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="cb_person_cred_hist_length" label={t('loanApplication.step2.credHistLength')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <InputNumber style={{ width: '100%' }} min={0} size="large" />
                </Form.Item>
              </Col>
            </Row>
          </div>

          {/* STEP 2: Loan Details */}
          <div style={{ display: currentStep === 2 ? 'block' : 'none' }}>
            <Title level={4}>{t('loanApplication.step3.title')}</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
              {t('loanApplication.step3.description')}
            </Text>

            <Row gutter={24}>
              <Col xs={24} md={12}>
                <Form.Item name="loan_amnt" label={t('loanApplication.step3.amount')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <InputNumber style={{ width: '100%' }} min={0} size="large" formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} parser={value => Number(value!.replace(/\$\s?|(,*)/g, '')) as any} />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="loan_intent" label={t('loanApplication.step3.intent')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value="PERSONAL">{t('loanApplication.step3.personal')}</Option>
                    <Option value="EDUCATION">{t('loanApplication.step3.education')}</Option>
                    <Option value="MEDICAL">{t('loanApplication.step3.medical')}</Option>
                    <Option value="VENTURE">{t('loanApplication.step3.venture')}</Option>
                    <Option value="HOMEIMPROVEMENT">{t('loanApplication.step3.homeImprovement')}</Option>
                    <Option value="DEBTCONSOLIDATION">{t('loanApplication.step3.debtConsolidation')}</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="loan_grade" label={t('loanApplication.step3.grade')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value="A">{t('loanApplication.step3.gradeA')}</Option>
                    <Option value="B">{t('loanApplication.step3.gradeB')}</Option>
                    <Option value="C">{t('loanApplication.step3.gradeC')}</Option>
                    <Option value="D">{t('loanApplication.step3.gradeD')}</Option>
                    <Option value="E">{t('loanApplication.step3.gradeE')}</Option>
                    <Option value="F">{t('loanApplication.step3.gradeF')}</Option>
                    <Option value="G">{t('loanApplication.step3.gradeG')}</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="loan_int_rate" label={t('loanApplication.step3.intRate')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <InputNumber style={{ width: '100%' }} min={0} step={0.1} size="large" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="loan_term_months" label={t('loanApplication.step3.term', 'Kỳ hạn Vay (Tháng)')} rules={[{ required: true, message: t('loanApplication.errors.required') }]}>
                  <Select size="large">
                    <Option value={12}>{t('loanApplication.step3.month12', '12 tháng (1 năm)')}</Option>
                    <Option value={24}>{t('loanApplication.step3.month24', '24 tháng (2 năm)')}</Option>
                    <Option value={36}>{t('loanApplication.step3.month36', '36 tháng (3 năm - Mặc định)')}</Option>
                    <Option value={48}>{t('loanApplication.step3.month48', '48 tháng (4 năm)')}</Option>
                    <Option value={60}>{t('loanApplication.step3.month60', '60 tháng (5 năm)')}</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </div>
        </Form>

        {/* STEP 3: Result */}
        {currentStep === 3 && result && (
          <div style={{ marginTop: 24 }}>
            <Title level={4} style={{ textAlign: 'center', marginBottom: 24 }}>
              {t('loanApplication.result.title')}
            </Title>
            <CreditRiskAssessmentDashboard
              assessment={result.credit_risk_assessment}
              requestedAmount={form.getFieldValue('loan_amnt')}
              requestedRate={form.getFieldValue('loan_int_rate')}
              income={form.getFieldValue('person_income')}
              intent={form.getFieldValue('loan_intent')}
              applicationId={savedClientId || 'APP-2026-0882'}
              rawFeatures={form.getFieldsValue()}
              onApproveProbingLimit={handleSaveToDB}
              onModifyTerms={() => setCurrentStep(2)}
              onReject={() => message.info(t('loanApplication.buttons.reject'))}
            />
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 32, paddingTop: 24, borderTop: '1px solid #f0f0f0' }}>
          {currentStep > 0 && currentStep < 3 ? (
            <Button size="large" onClick={handlePrev} icon={<LeftOutlined />}>
              {t('loanApplication.buttons.prev')}
            </Button>
          ) : <div />}

          {currentStep < 2 && (
            <Button type="primary" size="large" onClick={handleNext}>
              {t('loanApplication.buttons.next')} <RightOutlined />
            </Button>
          )}

          {currentStep === 2 && (
            <Button type="primary" size="large" onClick={handleSubmit} loading={loading} icon={<SendOutlined />}>
              {t('loanApplication.buttons.submit')}
            </Button>
          )}

          {currentStep === 3 && (
            <div style={{ display: 'flex', gap: 16, margin: '0 auto' }}>
              <Button size="large" onClick={handleReset} icon={<ReloadOutlined />}>
                {t('loanApplication.buttons.reset')}
              </Button>
              <Button
                type="primary"
                size="large"
                onClick={handleSaveToDB}
                loading={saving}
                disabled={!!savedClientId}
                icon={savedClientId ? <CheckCircleOutlined /> : <DatabaseOutlined />}
              // style={{ backgroundColor: savedClientId ? '#52c41a' : undefined }}
              >
                {savedClientId ? t('loanApplication.buttons.created') : t('loanApplication.buttons.saveToDb')}
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
