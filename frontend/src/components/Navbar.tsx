import React from 'react';
import { ShieldCheck, Cpu } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon">
          <ShieldCheck size={22} color="#FFFFFF" />
        </div>
        <div>
          <span>CREDIT RISK AI</span>
          <span style={{ fontSize: '0.75rem', display: 'block', color: 'var(--text-muted)', fontWeight: 400 }}>
            Hệ thống Thu thập Khoản vay & Chấm điểm Tín dụng
          </span>
        </div>
      </div>

      <div className="navbar-badge">
        <div className="pulse-dot" />
        <Cpu size={14} />
        <span>ML Core Engine Active</span>
      </div>
    </header>
  );
};
