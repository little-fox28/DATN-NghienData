import { Button, message } from 'antd';
import { Download, RefreshCw } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getPortfolioSummary } from '../api/client';
import { LoanTermRiskCard } from '../components/dashboard/LoanTermRiskCard';
import { PortfolioExposureCard } from '../components/dashboard/PortfolioExposureCard';
import { PortfolioMetricCards } from '../components/dashboard/PortfolioMetricCards';
import { RiskTierDistributionCard } from '../components/dashboard/RiskTierDistributionCard';
import type { PortfolioSummaryResponse } from '../types/loan';

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(true);
  const [summaryData, setSummaryData] = useState<PortfolioSummaryResponse | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const summaryRes = await getPortfolioSummary();
      setSummaryData(summaryRes);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      message.error(t('dashboard.errors.loadFailed', 'Không thể tải dữ liệu dashboard.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleExportCSV = () => {
    window.open(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/enrich/export`, '_blank');
  };

  return (
    <div className="w-full space-y-6 pb-8">
      {/* 1. Header Workspace Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 dark:border-[#2a2a2a]">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight mt-1">
            {t('dashboard.title', 'Bảng Điều Khiển Quản Trị Rủi Ro Tín Dụng')}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('dashboard.subtitle', 'Giám sát Danh mục Cho vay, Phân tích XAI Đóng góp WoE và Hàng đợi Thẩm định Rủi ro')}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            icon={<RefreshCw className="w-3.5 h-3.5" />}
            onClick={fetchDashboardData}
            loading={loading}
            className="flex items-center gap-1.5 font-medium"
          >
            {t('dashboard.buttons.refresh', 'Làm mới')}
          </Button>

          <Button
            type="primary"
            icon={<Download className="w-3.5 h-3.5" />}
            onClick={handleExportCSV}
            className="bg-indigo-600 hover:bg-indigo-500 border-none font-medium flex items-center gap-1.5"
          >
            {t('dashboard.buttons.export', 'Xuất Báo Cáo (CSV)')}
          </Button>
        </div>
      </div>

      {/* 2. Tầng 1: Executive Portfolio Pulse (5 KPIs) */}
      <section>
        <PortfolioMetricCards kpis={summaryData?.kpis} loading={loading} />
      </section>

      {/* 3. Tầng 2: Risk Drivers & Portfolio Segmentation */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskTierDistributionCard
          riskTiers={summaryData?.risk_tiers}
          grades={summaryData?.grades}
          loading={loading}
        />
        <LoanTermRiskCard
          terms={summaryData?.terms}
          loading={loading}
        />
      </section>

      {/* 4. Portfolio Exposure Concentration */}
      <section>
        <PortfolioExposureCard
          intents={summaryData?.intents}
          homeOwnership={summaryData?.home_ownership}
          loading={loading}
        />
      </section>
    </div>
  );
};
