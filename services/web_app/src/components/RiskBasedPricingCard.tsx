import React from 'react';
import { Card, Row, Col, Typography, Tag, Progress, Space, Statistic, Divider } from 'antd';
import {
  DollarOutlined,
  CalendarOutlined,
  ArrowDownOutlined,
  ArrowUpOutlined,
  CheckCircleFilled,
  ExclamationCircleFilled,
  CloseCircleFilled,
  SafetyCertificateOutlined,
  BankOutlined,
  SolutionOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import type { RiskBasedPricingRecommendation } from '../types/loan';

const { Title, Text } = Typography;

interface RiskBasedPricingCardProps {
  pricing?: RiskBasedPricingRecommendation;
  requestedRate?: number;
  riskTier?: string;
}

export const RiskBasedPricingCard: React.FC<RiskBasedPricingCardProps> = ({
  pricing,
  requestedRate,
  riskTier = 'LOW',
}) => {
  const { t } = useTranslation();

  if (!pricing) {
    return null;
  }

  const {
    recommended_interest_rate,
    base_rate,
    risk_spread,
    capital_discount,
    intent_adjustment,
    max_credit_limit,
    requested_amount,
    limit_status,
    loan_term_months = 36,
    monthly_payment_estimate = 0,
    total_interest_estimate = 0,
  } = pricing;

  // Rate delta comparison vs customer requested rate
  const rateDelta = requestedRate ? (recommended_interest_rate - requestedRate) : 0;
  const isSavings = rateDelta < 0;

  // Credit Limit Percentage calculation
  const limitPercent = max_credit_limit > 0
    ? Math.min(Math.round((requested_amount / max_credit_limit) * 100), 100)
    : 100;

  // Status tag config
  const getLimitStatusTag = () => {
    switch (limit_status) {
      case 'WITHIN_LIMIT':
        return (
          <Tag color="success" icon={<CheckCircleFilled />}>
            {t('pricing.limitStatus.withinLimit')}
          </Tag>
        );
      case 'EXCEEDS_RECOMMENDED_LIMIT':
        return (
          <Tag color="warning" icon={<ExclamationCircleFilled />}>
            {t('pricing.limitStatus.exceedsLimit')}
          </Tag>
        );
      case 'REJECTED':
        return (
          <Tag color="error" icon={<CloseCircleFilled />}>
            {t('pricing.limitStatus.rejected')}
          </Tag>
        );
      default:
        return null;
    }
  };

  // Color scheme based on risk tier
  const getTierColor = () => {
    switch (riskTier) {
      case 'LOW':
        return '#52c41a';
      case 'MEDIUM_LOW':
        return '#1677ff';
      case 'MEDIUM_HIGH':
        return '#faad14';
      case 'HIGH':
        return '#ff4d4f';
      default:
        return '#1677ff';
    }
  };

  return (
    <Card
      style={{
        marginTop: 24,
        borderRadius: 16,
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
        border: '1px solid rgba(22, 119, 255, 0.15)',
        overflow: 'hidden',
      }}
      bodyStyle={{ padding: 24 }}
    >
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Space size={10}>
          <SafetyCertificateOutlined style={{ fontSize: 24, color: getTierColor() }} />
          <div>
            <Title level={4} style={{ margin: 0 }}>
              {t('pricing.title')}
            </Title>
            <Text type="secondary" style={{ fontSize: 13 }}>
              {t('pricing.subtitle')}
            </Text>
          </div>
        </Space>
        {getLimitStatusTag()}
      </div>

      <Divider style={{ margin: '12px 0 20px 0' }} />

      {/* Main Grid: APR Badge & Payment Summary */}
      <Row gutter={[24, 24]}>
        {/* Left Column: APR Badge & Rate Breakdown */}
        <Col xs={24} lg={12}>
          <Card
            type="inner"
            style={{
              background: 'linear-gradient(135deg, rgba(22, 119, 255, 0.05) 0%, rgba(82, 196, 26, 0.05) 100%)',
              borderColor: 'rgba(22, 119, 255, 0.2)',
              borderRadius: 12,
              textAlign: 'center',
              padding: 16,
            }}
          >
            <Text type="secondary" style={{ textTransform: 'uppercase', letterSpacing: 1, fontSize: 12, fontWeight: 600 }}>
              {t('pricing.recommendedAprLabel')}
            </Text>
            <div style={{ margin: '8px 0' }}>
              <Title level={1} style={{ margin: 0, color: getTierColor(), fontSize: 42, lineHeight: 1 }}>
                {recommended_interest_rate.toFixed(2)}%
                <Text style={{ fontSize: 16, color: '#8c8c8c', marginLeft: 4 }}>/ {t('pricing.year')}</Text>
              </Title>
            </div>

            {/* Requested Rate Comparison Delta */}
            {requestedRate && Math.abs(rateDelta) > 0.01 && (
              <div style={{ marginTop: 8 }}>
                <Tag color={isSavings ? 'green' : 'orange'} style={{ fontSize: 12, padding: '4px 12px', borderRadius: 12 }}>
                  {isSavings ? <ArrowDownOutlined /> : <ArrowUpOutlined />}
                  {isSavings
                    ? t('pricing.savingsVsRequested', { delta: Math.abs(rateDelta).toFixed(2) })
                    : t('pricing.surchargeVsRequested', { delta: rateDelta.toFixed(2) })}
                </Tag>
              </div>
            )}

            <Divider style={{ margin: '16px 0 12px 0' }} />

            {/* Rate Breakdown Waterfall */}
            <div style={{ textAlign: 'left' }}>
              <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                <BankOutlined style={{ marginRight: 6 }} />
                {t('pricing.rateBreakdownTitle')}:
              </Text>
              <Space wrap size={[6, 8]}>
                <Tag color="blue">
                  {t('pricing.components.base')}: {base_rate.toFixed(2)}%
                </Tag>
                <Tag color={risk_spread > 3 ? 'volcano' : 'cyan'}>
                  {t('pricing.components.riskSpread')}: +{risk_spread.toFixed(2)}%
                </Tag>
                {capital_discount < 0 && (
                  <Tag color="green">
                    {t('pricing.components.capitalDiscount')}: {capital_discount.toFixed(2)}%
                  </Tag>
                )}
                {intent_adjustment !== 0 && (
                  <Tag color={intent_adjustment < 0 ? 'green' : 'orange'}>
                    {t('pricing.components.intentAdj')}: {intent_adjustment > 0 ? `+${intent_adjustment.toFixed(2)}%` : `${intent_adjustment.toFixed(2)}%`}
                  </Tag>
                )}
              </Space>
            </div>
          </Card>
        </Col>

        {/* Right Column: Monthly Repayment & Total Interest */}
        <Col xs={24} lg={12}>
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            {/* Repayment Simulation Box */}
            <Card
              type="inner"
              style={{
                borderRadius: 12,
                backgroundColor: 'rgba(250, 250, 250, 0.6)',
                borderColor: '#f0f0f0',
                marginBottom: 16,
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title={
                      <Space size={4}>
                        <CalendarOutlined />
                        <span>{t('pricing.monthlyPayment')}</span>
                      </Space>
                    }
                    value={monthly_payment_estimate}
                    precision={2}
                    prefix="$"
                    suffix={`/ ${t('pricing.month')}`}
                    valueStyle={{ color: '#1677ff', fontWeight: 'bold' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title={
                      <Space size={4}>
                        <DollarOutlined />
                        <span>{t('pricing.totalInterest')}</span>
                      </Space>
                    }
                    value={total_interest_estimate}
                    precision={2}
                    prefix="$"
                    valueStyle={{ color: '#cf1322', fontWeight: 600 }}
                  />
                </Col>
              </Row>
              <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
                * {t('pricing.amortizationNote', { term: loan_term_months })}
              </Text>
            </Card>

            {/* Credit Limit Allocation Progress Bar */}
            <div style={{ padding: '0 4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <Text strong style={{ fontSize: 13 }}>
                  <SolutionOutlined style={{ marginRight: 6 }} />
                  {t('pricing.creditLimitTitle')}:
                </Text>
                <Text style={{ fontSize: 13 }}>
                  <Text strong>${requested_amount.toLocaleString()}</Text> / ${max_credit_limit.toLocaleString()}
                </Text>
              </div>
              <Progress
                percent={limitPercent}
                status={limit_status === 'EXCEEDS_RECOMMENDED_LIMIT' ? 'exception' : 'active'}
                strokeColor={limit_status === 'EXCEEDS_RECOMMENDED_LIMIT' ? '#faad14' : '#52c41a'}
                showInfo={false}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {t('pricing.requested')}: ${requested_amount.toLocaleString()}
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {t('pricing.maxLimit')}: ${max_credit_limit.toLocaleString()}
                </Text>
              </div>
            </div>
          </div>
        </Col>
      </Row>

      {/* Exceeds limit advisory alert */}
      {limit_status === 'EXCEEDS_RECOMMENDED_LIMIT' && (
        <div
          style={{
            marginTop: 20,
            padding: '12px 16px',
            backgroundColor: '#fffbe6',
            border: '1px solid #ffe58f',
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <ExclamationCircleFilled style={{ color: '#faad14', fontSize: 18 }} />
          <Text style={{ fontSize: 13, color: '#873800' }}>
            {t('pricing.exceedsLimitAdvisory', { max: max_credit_limit.toLocaleString() })}
          </Text>
        </div>
      )}
    </Card>
  );
};
