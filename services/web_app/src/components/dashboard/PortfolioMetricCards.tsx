import { AlertTriangle, ArrowUpRight, DollarSign, FileClock, Percent, ShieldCheck } from 'lucide-react';
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import type { PortfolioKPIs } from '../../types/loan';

interface PortfolioMetricCardsProps {
  kpis?: PortfolioKPIs;
  loading?: boolean;
}

export const PortfolioMetricCards: React.FC<PortfolioMetricCardsProps> = ({ kpis, loading }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const volume = kpis?.total_loan_volume ?? 312431300;
  const defaultRate = kpis?.overall_default_rate ?? 21.82;
  const avgRate = kpis?.avg_interest_rate ?? 11.01;
  const avgFico = kpis?.avg_fico_score ?? 674;
  const pendingReviews = kpis?.pending_manual_reviews ?? 10084;

  const cards = [
    {
      title: t('dashboard.kpi.totalVolume', 'Tổng Dư Nợ Danh Mục'),
      value: `$${(volume / 1_000_000).toFixed(1)}M`,
      subtext: `${kpis?.total_applications?.toLocaleString() ?? '32,581'} ${t('dashboard.kpi.applications', 'hồ sơ')}`,
      icon: DollarSign,
      iconColor: 'text-blue-500 bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900/60',
      badge: '+8.4% QoQ',
      badgePositive: true,
      clickable: false,
    },
    {
      title: t('dashboard.kpi.defaultRate', 'Tỷ Lệ Nợ Xấu (NPL)'),
      value: `${defaultRate.toFixed(2)}%`,
      subtext: t('dashboard.kpi.riskAppetite', 'Khẩu vị rủi ro: < 22%'),
      icon: AlertTriangle,
      iconColor: 'text-rose-500 bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-900/60',
      badge: defaultRate <= 22 ? t('dashboard.kpi.badgeStable', 'Ổn định') : t('dashboard.kpi.badgeWarning', 'Cảnh báo'),
      badgePositive: defaultRate <= 22,
      clickable: false,
    },
    {
      title: t('dashboard.kpi.avgRate', 'Lãi Suất Bình Quân (APR)'),
      value: `${avgRate.toFixed(2)}%`,
      subtext: t('dashboard.kpi.riskAdjusted', 'Biên độ bù đắp rủi ro'),
      icon: Percent,
      iconColor: 'text-teal-500 bg-teal-50 dark:bg-teal-950/40 border-teal-200 dark:border-teal-900/60',
      badge: '5.4% - 23.2%',
      badgePositive: true,
      clickable: false,
    },
    {
      title: t('dashboard.kpi.avgFico', 'Điểm FICO Bình Quân'),
      value: `${avgFico}`,
      subtext: t('dashboard.kpi.ficoTier', 'Phân hạng: Standard Tier'),
      icon: ShieldCheck,
      iconColor: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/60',
      badge: t('dashboard.kpi.tierB', 'Tier B'),
      badgePositive: true,
      clickable: false,
    },
    {
      title: t('dashboard.kpi.manualQueue', 'Hồ Sơ Cần Thẩm Định'),
      value: `${pendingReviews.toLocaleString()}`,
      subtext: t('dashboard.kpi.borderlineDesc', 'Vùng đệm rủi ro (Grade C-D)'),
      icon: FileClock,
      iconColor: 'text-amber-500 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/60',
      badge: t('dashboard.kpi.actionRequired', 'Cần rà soát'),
      badgePositive: false,
      clickable: true,
      onClick: () => navigate('/underwriting?source=backlog'),
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((card, idx) => {
        const IconComponent = card.icon;
        return (
          <div
            key={idx}
            onClick={card.clickable ? card.onClick : undefined}
            className={`bg-white dark:bg-[#141414] rounded-lg border border-gray-200 dark:border-[#2a2a2a] p-4 shadow-xs flex flex-col justify-between transition-all ${
              card.clickable
                ? 'cursor-pointer hover:border-amber-400 dark:hover:border-amber-500/80 hover:shadow-md group'
                : 'hover:border-gray-300 dark:hover:border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {card.title}
                </span>
                {card.clickable && (
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-amber-500 transition-colors" />
                )}
              </div>
              <div className={`p-2 rounded-lg border ${card.iconColor}`}>
                <IconComponent className="w-4 h-4" />
              </div>
            </div>

            <div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight font-mono">
                {loading ? '...' : card.value}
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 dark:border-[#262626] text-xs">
                <span className="text-gray-500 dark:text-gray-400 truncate mr-2">
                  {card.subtext}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold whitespace-nowrap transition-colors ${
                    card.badgePositive
                      ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/60'
                      : card.clickable
                      ? 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-900/60 group-hover:bg-amber-500 group-hover:text-white'
                      : 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-900/60'
                  }`}
                >
                  {card.badge}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
