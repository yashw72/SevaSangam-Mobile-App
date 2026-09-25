import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import i18n, {
  SUPPORTED_LANGUAGES,
  DEFAULT_LANGUAGE,
  getPersistedLanguage,
  changeAppLanguage,
} from '../i18n';

export const LanguageContext = createContext({
  currentLanguage: DEFAULT_LANGUAGE,
  changeLanguage: async () => {},
  isLanguageLoading: true,
  supportedLanguages: SUPPORTED_LANGUAGES,
  t: (key, options) => key,
});

export const LanguageProvider = ({ children }) => {
  const [currentLanguage, setCurrentLanguage] = useState(i18n.language || DEFAULT_LANGUAGE);
  const [isLanguageLoading, setIsLanguageLoading] = useState(true);

  // Restore persisted language on startup
  useEffect(() => {
    let isMounted = true;

    const restoreLanguage = async () => {
      try {
        const savedLanguage = await getPersistedLanguage();
        if (savedLanguage && savedLanguage !== i18n.language) {
          await i18n.changeLanguage(savedLanguage);
          if (isMounted) {
            setCurrentLanguage(savedLanguage);
          }
        } else if (isMounted) {
          setCurrentLanguage(i18n.language || DEFAULT_LANGUAGE);
        }
      } catch (error) {
        console.warn('[LanguageContext] Failed to restore language:', error);
      } finally {
        if (isMounted) {
          setIsLanguageLoading(false);
        }
      }
    };

    restoreLanguage();

    const handleLanguageChanged = (lng) => {
      if (isMounted) {
        setCurrentLanguage(lng);
      }
    };

    i18n.on('languageChanged', handleLanguageChanged);

    return () => {
      isMounted = false;
      i18n.off('languageChanged', handleLanguageChanged);
    };
  }, []);

  // Instant language change without app reload
  const changeLanguage = useCallback(async (newLanguageCode) => {
    try {
      await changeAppLanguage(newLanguageCode);
      setCurrentLanguage(newLanguageCode);
    } catch (error) {
      console.error('[LanguageContext] Error changing language:', error);
    }
  }, []);

  const value = {
    currentLanguage,
    changeLanguage,
    isLanguageLoading,
    supportedLanguages: SUPPORTED_LANGUAGES,
    t: i18n.t.bind(i18n),
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export default LanguageContext;
