import { BgColorsOutlined, GlobalOutlined } from '@ant-design/icons';
import { Layout, Select, Space, theme } from 'antd';
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAppContext } from '../contexts/AppProvider';

const { Header } = Layout;

export const Navbar: React.FC = () => {
  const {
    token: { colorBgContainer, colorText, colorBorderSecondary },
  } = theme.useToken();
  const { language, setLanguage, themeMode, setThemeMode } = useAppContext();
  const { t } = useTranslation();

  return (
    <Header style={{ background: colorBgContainer, padding: '0 24px', display: 'flex', alignItems: 'center', borderBottom: `1px solid ${colorBorderSecondary}`, lineHeight: 'normal' }}>
      <div className="header-container">
        <div className="brand-section">
          <img src='/logo.png' alt='logo' width={90} height={"auto"} />
          <div>
            <h1 className="brand-title" style={{ color: colorText }}>{t('navbar.title')}</h1>
            <span className="brand-subtitle">
              {t('navbar.subtitle')}
            </span>
          </div>
        </div>
        <div className="actions-section">
          <Space size="middle">
            <Select
              value={language}
              onChange={setLanguage}
              style={{ width: 130 }}
              suffixIcon={<GlobalOutlined />}
              options={[
                { value: 'vi', label: t('settings.vi') },
                { value: 'en', label: t('settings.en') },
              ]}
            />
            <Select
              value={themeMode}
              onChange={setThemeMode}
              style={{ width: 130 }}
              suffixIcon={<BgColorsOutlined />}
              options={[
                { value: 'light', label: t('settings.light') },
                { value: 'dark', label: t('settings.dark') },
                { value: 'system', label: t('settings.system') },
              ]}
            />
          </Space>
        </div>
      </div>
    </Header>
  );
};
