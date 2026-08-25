import { Layers } from 'lucide-react';
import React from 'react';
import { useTranslation } from 'react-i18next';
import type { GradeItem, RiskTierItem } from '../../types/loan';

interface RiskTierDistributionCardProps {
  riskTiers?: RiskTierItem[];
  grades?: GradeItem[];
  loading?: boolean;
}

export const RiskTierDistributionCard: React.FC<RiskTierDistributionCardProps> = ({
  riskTiers,
  grades,
}) => {
  const { t } = useTranslation();

  const getTierDisplayName = (tier: string) => {
    switch (tier.toUpperCase()) {
      case 'LOW':
        return t('dashboard.riskTiers.tierLow', 'Rất Thấp (Prime)');
      case 'MEDIUM_LOW':
        return t('dashboard.riskTiers.tierMedLow', 'Thấp - Tiêu Chuẩn');
      case 'MEDIUM_HIGH':
        return t('dashboard.riskTiers.tierMedHigh', 'Trung Bình Cao');
      case 'HIGH':
        return t('dashboard.riskTiers.tierHigh', 'Rủi Ro Cao (Subprime)');
      default:
        return tier;
    }
  };

  const rawTiers: RiskTierItem[] = riskTiers && riskTiers.length > 0 ? riskTiers : [
    { tier: 'LOW', name: '', fico_range: '>= 740', pct: 33.1, color: '#10B981', decision: 'APPROVED' },
    { tier: 'MEDIUM_LOW', name: '', fico_range: '670 - 739', pct: 32.1, color: '#0D9488', decision: 'APPROVED_CONDITIONAL' },
    { tier: 'MEDIUM_HIGH', name: '', fico_range: '580 - 669', pct: 19.8, color: '#F59E0B', decision: 'MANUAL_REVIEW' },
    { tier: 'HIGH', name: '', fico_range: '< 580', pct: 15.0, color: '#F43F5E', decision: 'REJECTED' },
  ];

  const defaultTiers = rawTiers.map((item) => ({
    ...item,
    name: getTierDisplayName(item.tier),
  }));

  const defaultGrades: GradeItem[] = grades && grades.length > 0 ? grades : [
    { grade: 'A', count: 10777, pct: 33.1, volume: 92027750, avg_rate: 7.33, default_rate: 9.96 },
    { grade: 'B', count: 10451, pct: 32.1, volume: 104462800, avg_rate: 11.00, default_rate: 16.28 },
    { grade: 'C', count: 6458, pct: 19.8, volume: 59503125, avg_rate: 13.46, default_rate: 20.73 },
    { grade: 'D', count: 3626, pct: 11.1, volume: 39339350, avg_rate: 15.36, default_rate: 59.05 },
    { grade: 'E', count: 964, pct: 3.0, volume: 12450875, avg_rate: 17.01, default_rate: 64.42 },
    { grade: 'F', count: 241, pct: 0.7, volume: 3546875, avg_rate: 18.61, default_rate: 70.54 },
    { grade: 'G', count: 64, pct: 0.2, volume: 1100525, avg_rate: 20.25, default_rate: 98.44 },
  ];

  return (
    <div className="bg-white dark:bg-[#141414] rounded-lg border border-gray-200 dark:border-[#2a2a2a] p-4 shadow-xs transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-900/60">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide">
              {t('dashboard.riskTiers.title', 'Phân Tầng Rủi Ro & Phễu Quyết Định')}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t('dashboard.riskTiers.subtitle', 'Phân bổ theo Chuẩn Thang điểm FICO và Chính sách Phê duyệt ML')}
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-gray-100 dark:bg-[#1f1f1f] text-gray-700 dark:text-gray-300">
          32,581 {t('dashboard.riskTiers.records', 'hồ sơ')}
        </span>
      </div>

      {/* 1. Stacked Segmented Bar */}
      <div className="mb-4">
        <div className="flex h-3.5 w-full rounded-full overflow-hidden gap-0.5 bg-gray-100 dark:bg-[#1f1f1f] p-0.5">
          {defaultTiers.map((tItem, idx) => (
            <div
              key={idx}
              style={{ width: `${tItem.pct}%`, backgroundColor: tItem.color }}
              className="h-full rounded-sm transition-all duration-500 hover:opacity-90"
              title={`${tItem.name}: ${tItem.pct}%`}
            />
          ))}
        </div>
      </div>

      {/* 2. Tier Legend & Details Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {defaultTiers.map((item, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg border border-gray-100 dark:border-[#262626] bg-gray-50/70 dark:bg-[#1a1a1a] flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-slate-800 dark:text-gray-200 truncate" title={item.name}>
                {item.name}
              </span>
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: item.color }}
              />
            </div>
            <div className="flex items-baseline justify-between text-xs">
              <span className="font-bold text-slate-900 dark:text-white text-sm">
                {item.pct}%
              </span>
              <span className="text-gray-500 dark:text-gray-400 font-mono text-[11px]">
                {item.fico_range}
              </span>
            </div>
            <div className="mt-1 text-[10px] text-gray-500 dark:text-gray-400 truncate">
              {item.decision}
            </div>
          </div>
        ))}
      </div>

      {/* 3. Loan Grade (A -> G) Escalation Table */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-bold text-slate-700 dark:text-gray-300 uppercase tracking-wider">
            {t('dashboard.riskTiers.gradeEscalation', 'Ma Trận Leo Thang Rủi Ro theo Hạng Tín Dụng (A → G)')}
          </h4>
          <span className="text-[11px] text-gray-400 dark:text-gray-500">
            {t('dashboard.riskTiers.nplRatio', 'Tỷ lệ nợ xấu tăng vọt từ Grade D')}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-[#2a2a2a] text-gray-400 dark:text-gray-500 font-medium">
                <th className="pb-2">{t('dashboard.table.grade', 'Hạng')}</th>
                <th className="pb-2 text-right">{t('dashboard.table.count', 'Số hồ sơ')}</th>
                <th className="pb-2 text-right">{t('dashboard.table.volume', 'Dư nợ ($)')}</th>
                <th className="pb-2 text-right">{t('dashboard.table.avgRate', 'Lãi suất TB')}</th>
                <th className="pb-2 text-right">{t('dashboard.table.defaultRate', 'Tỷ lệ Nợ Xấu (NPL)')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-[#262626] font-mono">
              {defaultGrades.map((g) => {
                const isHighRisk = g.default_rate > 50;
                return (
                  <tr key={g.grade} className="hover:bg-gray-50 dark:hover:bg-[#1f1f1f]/60 transition-colors">
                    <td className="py-1.5 font-sans font-bold flex items-center gap-1.5">
                      <span
                        className={`w-5 h-5 rounded flex items-center justify-center text-xs font-bold ${g.grade === 'A' || g.grade === 'B'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300'
                            : g.grade === 'C'
                              ? 'bg-teal-100 text-teal-800 dark:bg-teal-950/80 dark:text-teal-300'
                              : g.grade === 'D'
                                ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300'
                                : 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'
                          }`}
                      >
                        {g.grade}
                      </span>
                    </td>
                    <td className="py-1.5 text-right text-slate-700 dark:text-gray-300">
                      {g.count.toLocaleString()} <span className="text-[10px] text-gray-400">({g.pct}%)</span>
                    </td>
                    <td className="py-1.5 text-right text-slate-700 dark:text-gray-300">
                      ${(g.volume / 1_000_000).toFixed(1)}M
                    </td>
                    <td className="py-1.5 text-right text-slate-700 dark:text-gray-300">
                      {g.avg_rate.toFixed(2)}%
                    </td>
                    <td className="py-1.5 text-right">
                      <span
                        className={`inline-flex items-center font-bold px-1.5 py-0.5 rounded text-[11px] ${isHighRisk
                            ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400'
                            : g.default_rate < 15
                              ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400'
                              : 'bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400'
                          }`}
                      >
                        {g.default_rate.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
