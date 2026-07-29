import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import vi from './locales/vi.json';
import en from './locales/en.json';

const savedLanguage = localStorage.getItem('app-language') || 'vi';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      vi: { translation: vi }
    },
    lng: savedLanguage,
    fallbackLng: 'vi',
    interpolation: {
      escapeValue: false // react already safes from xss
    }
  });

export default i18n;
