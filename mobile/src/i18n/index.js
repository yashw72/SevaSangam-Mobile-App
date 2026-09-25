import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as SecureStore from 'expo-secure-store';

import en from './locales/en.json';
import hi from './locales/hi.json';
import mr from './locales/mr.json';

export const LANGUAGE_STORAGE_KEY = 'sevasangam_user_language';
export const DEFAULT_LANGUAGE = 'en';

export const SUPPORTED_LANGUAGES = [
  {
    code: 'en',
    label: 'English',
    nativeName: 'English',
    script: 'Latin',
  },
  {
    code: 'hi',
    label: 'Hindi',
    nativeName: 'हिन्दी',
    script: 'Devanagari',
  },
  {
    code: 'mr',
    label: 'Marathi',
    nativeName: 'मराठी',
    script: 'Devanagari',
  },
];

const resources = {
  en,
  hi,
  mr,
};

/**
 * Safely retrieves persisted language code from expo-secure-store
 */
export const getPersistedLanguage = async () => {
  try {
    const isAvailable = await SecureStore.isAvailableAsync?.();
    if (isAvailable === false) {
      return null;
    }
    const savedLang = await SecureStore.getItemAsync(LANGUAGE_STORAGE_KEY);
    if (savedLang && SUPPORTED_LANGUAGES.some((lang) => lang.code === savedLang)) {
      return savedLang;
    }
  } catch (error) {
    console.warn('[i18n] Could not read persisted language from SecureStore:', error);
  }
  return null;
};

/**
 * Safely persists user's selected language in expo-secure-store
 */
export const persistLanguage = async (languageCode) => {
  try {
    const isAvailable = await SecureStore.isAvailableAsync?.();
    if (isAvailable === false) {
      return;
    }
    await SecureStore.setItemAsync(LANGUAGE_STORAGE_KEY, languageCode);
  } catch (error) {
    console.warn('[i18n] Could not persist language to SecureStore:', error);
  }
};

/**
 * Changes active language instantly and persists to SecureStore
 */
export const changeAppLanguage = async (languageCode) => {
  if (!SUPPORTED_LANGUAGES.some((lang) => lang.code === languageCode)) {
    console.warn(`[i18n] Unsupported language requested: ${languageCode}`);
    return i18n.language;
  }
  await i18n.changeLanguage(languageCode);
  await persistLanguage(languageCode);
  return languageCode;
};

/**
 * Ensures missing keys resolve gracefully instead of rendering raw technical keys
 */
const formatMissingKeyFallback = (key) => {
  if (!key || typeof key !== 'string') return '';
  const segments = key.split('.');
  const rawWord = segments[segments.length - 1];
  return rawWord
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

i18n
  .use(initReactI18next)
  .init({
    compatibilityJSON: 'v4',
    resources,
    lng: DEFAULT_LANGUAGE,
    fallbackLng: 'en',
    ns: ['common', 'auth', 'customer', 'worker', 'admin', 'errors', 'status'],
    defaultNS: 'common',
    interpolation: {
      escapeValue: false, // React Native handles XSS safely
    },
    react: {
      useSuspense: false,
    },
    returnNull: false,
    returnEmptyString: false,
    parseMissingKeyHandler: (key) => formatMissingKeyFallback(key),
  });

export default i18n;
