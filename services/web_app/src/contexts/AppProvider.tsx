import React, { createContext, useContext, useEffect, useState } from 'react';
import { ConfigProvider, theme as antdTheme, App as AntApp } from 'antd';
import viVN from 'antd/locale/vi_VN';
import enUS from 'antd/locale/en_US';
import { useTranslation } from 'react-i18next';
import '../i18n/config'; // initialize i18n

type ThemeMode = 'light' | 'dark' | 'system';
type Language = 'vi' | 'en';

interface AppContextType {
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  isDarkMode: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { i18n } = useTranslation();
  const [themeMode, setThemeModeState] = useState<ThemeMode>(() => {
    return (localStorage.getItem('app-theme') as ThemeMode) || 'system';
  });
  const [language, setLanguageState] = useState<Language>(() => {
    return (localStorage.getItem('app-language') as Language) || 'vi';
  });
  const [systemIsDark, setSystemIsDark] = useState<boolean>(() => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemIsDark(e.matches);
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const setThemeMode = (mode: ThemeMode) => {
    setThemeModeState(mode);
    localStorage.setItem('app-theme', mode);
  };

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('app-language', lang);
    i18n.changeLanguage(lang);
  };

  const isDarkMode = themeMode === 'dark' || (themeMode === 'system' && systemIsDark);

  return (
    <AppContext.Provider value={{ themeMode, setThemeMode, language, setLanguage, isDarkMode }}>
      <ConfigProvider
        locale={language === 'en' ? enUS : viVN}
        theme={{
          algorithm: isDarkMode ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
          token: {
            colorPrimary: '#00afee', // M├áu Cyan cß╗ºa chß╗» NOVA
            colorInfo: '#00afee',
            colorTextBase: isDarkMode ? undefined : '#1d255f', // M├áu Navy cß╗ºa icon v├á chß╗» BANK l├ám m├áu chß╗» ch├¡nh (chß╗ë ß╗ƒ Light mode)
          },
        }}
      >
        <AntApp>
          {children}
        </AntApp>
      </ConfigProvider>
    </AppContext.Provider>
  );
};
