import React from 'react';
import { Typography, Card, Row, Col, Statistic } from 'antd';
import { CheckCircleOutlined, WarningOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { Title, Paragraph } = Typography;

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <Title level={2}>{t('dashboard.title')}</Title>
      <Paragraph>
        {t('dashboard.welcome')}
      </Paragraph>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card bordered={false} className="form-container-card">
            <Statistic
              title={t('dashboard.stats.processed')}
              value={1128}
              valueStyle={{ color: '#1677ff' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={false} className="form-container-card">
            <Statistic
              title={t('dashboard.stats.highRisk')}
              value={93}
              valueStyle={{ color: '#cf1322' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered={false} className="form-container-card">
            <Statistic
              title={t('dashboard.stats.reappraisal')}
              value={12}
              valueStyle={{ color: '#faad14' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: 40, textAlign: 'center', color: '#8c8c8c' }}>
        <p>{t('dashboard.futureNote')}</p>
      </div>
    </div>
  );
};
