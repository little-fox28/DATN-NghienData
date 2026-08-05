import { Alert, Card, Col, Row, Typography, theme } from 'antd';
import React from 'react';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;

interface CreditScoreGaugeProps {
  score: number;       // 381 to 553 (or custom)
  minScore?: number;   // Default 381
  maxScore?: number;   // Default 553
  pdScore: number;     // 0 to 1
  riskTier: string;
  decision: string;
}

export const CreditScoreGauge: React.FC<CreditScoreGaugeProps> = ({
  score,
  minScore = 300,
  maxScore = 850,
  pdScore,
  riskTier,
  decision,
}) => {
  const { t } = useTranslation();
  const { token } = theme.useToken();

  // Normalize score to percentage based on FICO scale (300 to 850)
  const percentage = Math.min(Math.max(((score - minScore) / (maxScore - minScore)) * 100, 0), 100);

  const getDecisionAlert = () => {
    switch (decision) {
      case 'APPROVED':
        return <Alert message={t('gauge.decision.approved')} type="success" showIcon />;
      case 'APPROVED_CONDITIONAL':
        return <Alert message={t('gauge.decision.approved_conditional')} type="info" showIcon />;
      case 'MANUAL_REVIEW':
        return <Alert message={t('gauge.decision.manual')} type="warning" showIcon />;
      case 'REJECTED':
      default:
        return <Alert message={t('gauge.decision.rejected')} type="error" showIcon />;
    }
  };

  const getPdColor = (pd: number) => {
    if (pd < 0.1) return '#52c41a'; // Xanh lá
    if (pd < 0.25) return '#faad14'; // Vàng cam
    return '#f5222d'; // Đỏ
  };

  const getTierColor = (tier: string) => {
    const tTier = tier.toUpperCase();
    if (tTier === 'A' || tTier === 'LOW') return '#52c41a'; // Xanh lá
    if (tTier === 'B' || tTier === 'MEDIUM_LOW') return '#1677ff'; // Xanh dương (Blue)
    if (tTier === 'C' || tTier === 'D' || tTier === 'MEDIUM_HIGH') return '#faad14'; // Vàng cam
    return '#f5222d'; // Đỏ (HIGH, CRITICAL)
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px' }}>
      <div style={{ width: '100%' }}>
        {getDecisionAlert()}
      </div>

      <div style={{ position: 'relative', width: '220px', height: '140px', marginTop: '16px' }}>
        <svg width="220" height="140" viewBox="0 0 200 120">
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={token.colorFillAlter}
            strokeWidth="16"
            strokeLinecap="round"
          />
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="16"
            strokeLinecap="round"
            strokeDasharray="251.2"
            strokeDashoffset={251.2 - (251.2 * percentage) / 100}
            style={{ transition: 'stroke-dashoffset 1.5s ease-out' }}
          />
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#EF4444" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#10B981" />
            </linearGradient>
          </defs>
        </svg>
        <div style={{ position: 'absolute', bottom: '10px', left: '0', right: '0', textAlign: 'center' }}>
          <div style={{
            fontSize: '3rem',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #1677ff, #52c41a)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            {score}
          </div>
          <span style={{ fontSize: '13px', color: token.colorTextSecondary }}>
            {t('gauge.scale', { min: minScore, max: maxScore })}
          </span>
        </div>
      </div>

      <Row gutter={16} style={{ width: '100%' }}>
        <Col span={12}>
          <Card bordered={false} style={{ backgroundColor: token.colorFillAlter }} bodyStyle={{ padding: '16px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>{t('gauge.pdScore')}</Text>
            <Title level={3} style={{ margin: 0, color: getPdColor(pdScore) }}>
              {(pdScore * 100).toFixed(2)}%
            </Title>
          </Card>
        </Col>
        <Col span={12}>
          <Card bordered={false} style={{ backgroundColor: token.colorFillAlter }} bodyStyle={{ padding: '16px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>{t('gauge.riskTier')}</Text>
            <Title level={3} style={{ margin: 0, color: getTierColor(riskTier) }}>
              {t('gauge.tierName', { tier: riskTier })}
            </Title>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
