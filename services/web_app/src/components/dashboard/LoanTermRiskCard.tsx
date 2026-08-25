import { Calendar } from 'lucide-react';
import React from 'react';
import { useTranslation } from 'react-i18next';
import type { TermItem } from '../../types/loan';

interface LoanTermRiskCardProps {
  terms?: TermItem[];
  loading?: boolean;
}

export const LoanTermRiskCard: React.FC<LoanTermRiskCardProps> = ({ terms }) => {
  const { t } = useTranslation();

  const defaultTerms: TermItem[] = terms && terms.length > 0 ? terms : [
    { term_months: 12, count: 3340, pct: 10.3, volume: 32000000, default_rate: 19.94, woe_points: 0.38 },
    { term_months: 24, count: 6374, pct: 19.6, volume: 61000000, default_rate: 22.09, woe_points: -0.07 },
    { term_months: 36, count: 12944, pct: 39.7, volume: 124000000, default_rate: 21.76, woe_points: 0.03 },
    { term_months: 60, count: 9923, pct: 30.5, volume: 95000000, default_rate: 22.34, woe_points: -0.12 },
  ];

  return (
    <div className="bg-white dark:bg-[#141414] rounded-lg border border-gray-200 dark:border-[#2a2a2a] p-4 shadow-xs transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950/40 text-teal-600 dark:text-teal-400 border border-teal-200 dark:border-teal-900/60">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide">
              {t('dashboard.loanTerms.title', 'Tương Quan Kỳ Hạn Vay & Trọng Số WoE')}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t('dashboard.loanTerms.subtitle', 'Đóng góp điểm tín dụng FICO & Tỷ lệ nợ xấu tích lũy')}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {defaultTerms.map((item) => {
          const isPositive = item.woe_points >= 0;
          return (
            <div
              key={item.term_months}
              className="p-3 rounded-lg border border-gray-100 dark:border-[#262626] bg-gray-50/70 dark:bg-[#1a1a1a]"
            >
              <div className="flex items-center justify-between mb-1.5 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 dark:text-white text-sm">
                    {item.term_months} {t('pricing.month', 'tháng')}
                  </span>
                  <span className="text-gray-400 dark:text-gray-500 text-[11px]">
                    ({item.count.toLocaleString()} {t('dashboard.kpi.applications', 'hồ sơ')} - {item.pct}%)
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-slate-700 dark:text-gray-300">
                    NPL: <strong className="text-slate-900 dark:text-white">{item.default_rate.toFixed(2)}%</strong>
                  </span>
                  <span
                    className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[11px] font-bold font-mono ${isPositive
                        ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/60'
                        : 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900/60'
                      }`}
                  >
                    {isPositive ? '+' : ''}{item.woe_points} pts
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${item.term_months === 12
                      ? 'bg-emerald-500'
                      : item.term_months === 36
                        ? 'bg-teal-500'
                        : item.term_months === 24
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                    }`}
                  style={{ width: `${item.pct * 2.2}%` }}
                />
              </div>

              <div className="flex justify-between items-center mt-1.5 text-[11px] text-gray-500 dark:text-gray-400">
                <span>{t('dashboard.loanTerms.volumePrefix', 'Dư nợ:')} ${(item.volume / 1_000_000).toFixed(1)}M</span>
                <span>
                  {item.term_months === 36
                    ? t('dashboard.loanTerms.note36', 'Kỳ hạn chuẩn ngân hàng')
                    : item.term_months === 12
                      ? t('dashboard.loanTerms.note12', 'Rủi ro thấp nhất (+0.38)')
                      : t('dashboard.loanTerms.noteLong', 'Rủi ro tích lũy kỳ hạn dài')}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
