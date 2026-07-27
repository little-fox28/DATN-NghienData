import React from 'react';

interface CreditScoreGaugeProps {
  score: number;       // 300 to 850
  pdScore: number;     // 0 to 1
  riskTier: string;
  decision: string;
}

export const CreditScoreGauge: React.FC<CreditScoreGaugeProps> = ({
  score,
  pdScore,
  riskTier,
  decision,
}) => {
  // Normalize score to percentage (300 to 850 scale)
  const percentage = Math.min(Math.max(((score - 300) / 550) * 100, 0), 100);
  
  const getDecisionClass = () => {
    switch (decision) {
      case 'APPROVED':
        return 'decision-approved';
      case 'MANUAL_REVIEW':
        return 'decision-review';
      case 'REJECTED':
      default:
        return 'decision-rejected';
    }
  };

  const getDecisionText = () => {
    switch (decision) {
      case 'APPROVED':
        return '✅ HỒ SƠ ĐƯỢC PHÊ DUYỆT TỰ ĐỘNG';
      case 'MANUAL_REVIEW':
        return '⚠️ CHUYỂN CÁN BỘ THẨM ĐỊNH THỦ CÔNG';
      case 'REJECTED':
      default:
        return '❌ HỒ SƠ BỊ TỪ CHỐI TỰ ĐỘNG';
    }
  };

  return (
    <div className="result-container">
      <div className={`decision-banner ${getDecisionClass()}`}>
        {getDecisionText()}
      </div>

      <div style={{ position: 'relative', width: '220px', height: '140px', marginTop: '1rem' }}>
        <svg width="220" height="140" viewBox="0 0 200 120">
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
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
        <div style={{ position: 'absolute', bottom: '10px', left: '0', right: '0' }}>
          <div className="score-badge">{score}</div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Thang điểm (300 - 850)</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', width: '100%', marginTop: '1rem' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Xác suất Vỡ nợ (PD)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#60A5FA', marginTop: '0.25rem' }}>
            {(pdScore * 100).toFixed(2)}%
          </div>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Phân hạng Rủi ro</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#34D399', marginTop: '0.25rem' }}>
            TIER {riskTier}
          </div>
        </div>
      </div>
    </div>
  );
};
