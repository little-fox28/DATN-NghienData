import { Briefcase, Home, PieChart } from 'lucide-react';
import React from 'react';
import { useTranslation } from 'react-i18next';
import type { HomeOwnershipItem, IntentItem } from '../../types/loan';

interface PortfolioExposureCardProps {
  intents?: IntentItem[];
  homeOwnership?: HomeOwnershipItem[];
  loading?: boolean;
}

export const PortfolioExposureCard: React.FC<PortfolioExposureCardProps> = ({
  intents,
  homeOwnership,
}) => {
  const { t } = useTranslation();

  const defaultIntents: IntentItem[] = intents && intents.length > 0 ? intents : [
    { intent: 'EDUCATION', count: 6453, pct: 19.8, volume: 61191725, default_rate: 17.22 },
    { intent: 'VENTURE', count: 5719, pct: 17.6, volume: 54809625, default_rate: 14.81 },
    { intent: 'PERSONAL', count: 5521, pct: 16.9, volume: 52856800, default_rate: 19.89 },
    { intent: 'DEBTCONSOLIDATION', count: 5212, pct: 16.0, volume: 50008550, default_rate: 28.59 },
    { intent: 'MEDICAL', count: 6071, pct: 18.6, volume: 56214925, default_rate: 26.70 },
    { intent: 'HOMEIMPROVEMENT', count: 3605, pct: 11.1, volume: 37349675, default_rate: 26.10 },
  ];

  const defaultHome: HomeOwnershipItem[] = homeOwnership && homeOwnership.length > 0 ? homeOwnership : [
    { ownership: 'RENT', count: 16446, pct: 50.5, volume: 157000000, default_rate: 31.57 },
    { ownership: 'MORTGAGE', count: 13444, pct: 41.3, volume: 129000000, default_rate: 12.57 },
    { ownership: 'OWN', count: 2584, pct: 7.9, volume: 24700000, default_rate: 7.47 },
    { ownership: 'OTHER', count: 107, pct: 0.3, volume: 1000000, default_rate: 30.84 },
  ];

  const getIntentLabel = (intentKey: string): string => {
    switch (intentKey.toUpperCase()) {
      case 'EDUCATION':
        return t('loanApplication.step3.education', 'Vay Học tập (EDUCATION)');
      case 'VENTURE':
        return t('loanApplication.step3.venture', 'Vay Kinh doanh (VENTURE)');
      case 'PERSONAL':
        return t('loanApplication.step3.personal', 'Vay Tiêu dùng (PERSONAL)');
      case 'DEBTCONSOLIDATION':
        return t('loanApplication.step3.debtConsolidation', 'Gộp nợ (DEBTCONSOLIDATION)');
      case 'MEDICAL':
        return t('loanApplication.step3.medical', 'Vay Y tế (MEDICAL)');
      case 'HOMEIMPROVEMENT':
        return t('loanApplication.step3.homeImprovement', 'Sửa chữa Nhà (HOMEIMPROVEMENT)');
      default:
        return intentKey;
    }
  };

  const getOwnershipLabel = (ownershipKey: string): string => {
    switch (ownershipKey.toUpperCase()) {
      case 'RENT':
        return t('dashboard.exposure.rent', 'Thuê nhà (RENT)');
      case 'MORTGAGE':
        return t('dashboard.exposure.mortgage', 'Thế chấp (MORTGAGE)');
      case 'OWN':
        return t('dashboard.exposure.own', 'Sở hữu riêng (OWN)');
      case 'OTHER':
        return t('dashboard.exposure.other', 'Khác (OTHER)');
      default:
        return ownershipKey;
    }
  };

  return (
    <div className="bg-white dark:bg-[#141414] rounded-lg border border-gray-200 dark:border-[#2a2a2a] p-4 shadow-xs transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-900/60">
            <PieChart className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide">
              {t('dashboard.exposure.title', 'Tập Trung Dư Nợ & Rủi Ro Theo Mục Đích Vay')}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t('dashboard.exposure.subtitle', 'Phân bổ danh mục theo Mục đích vay vốn & Tình trạng Nhà ở')}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left Column: Loan Intents */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 dark:text-gray-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Briefcase className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
            {t('dashboard.exposure.intentTitle', 'Mục đích Vay (Loan Intent)')}
          </h4>
          <div className="space-y-2">
            {defaultIntents.map((item) => (
              <div
                key={item.intent}
                className="flex items-center justify-between p-2 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626] text-xs"
              >
                <div className="flex flex-col">
                  <span className="font-semibold text-slate-800 dark:text-gray-200">
                    {getIntentLabel(item.intent)}
                  </span>
                  <span className="text-[10px] text-gray-400 dark:text-gray-500">
                    ${(item.volume / 1_000_000).toFixed(1)}M ({item.pct}%)
                  </span>
                </div>
                <div className="text-right">
                  <span
                    className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-bold font-mono ${item.default_rate < 18
                        ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50'
                        : item.default_rate < 25
                          ? 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50'
                          : 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50'
                      }`}
                  >
                    NPL: {item.default_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Home Ownership */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 dark:text-gray-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Home className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500" />
            {t('dashboard.exposure.housingTitle', 'Sở hữu Nhà ở (Home Ownership)')}
          </h4>
          <div className="space-y-2.5">
            {defaultHome.map((h) => (
              <div
                key={h.ownership}
                className="p-2.5 rounded-lg bg-gray-50/70 dark:bg-[#1a1a1a] border border-gray-100 dark:border-[#262626]"
              >
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-bold text-slate-800 dark:text-gray-200">
                    {getOwnershipLabel(h.ownership)}
                  </span>
                  <span className="font-mono text-slate-700 dark:text-gray-300 text-[11px]">
                    NPL: <strong>{h.default_rate.toFixed(1)}%</strong> ({h.pct}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${h.ownership === 'OWN'
                        ? 'bg-emerald-500'
                        : h.ownership === 'MORTGAGE'
                          ? 'bg-teal-500'
                          : 'bg-rose-500'
                      }`}
                    style={{ width: `${h.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
