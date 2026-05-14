// ============================================================================
// ArkheI18n — Sistema de Internacionalização para a Catedral
// Suporte a 50+ idiomas com fallback inteligente e tradução automática
// ============================================================================

import i18n from 'i18next';
import { initReactI18next, useTranslation } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';
import { TranslationService } from './services/TranslationService';
import { LocaleManager } from './LocaleManager';
import React, { useState, useEffect } from 'react';
import { Text } from 'react-native';

// ============================================================================
// CONFIGURAÇÃO DO I18NEXT
// ============================================================================

export const supportedLocales = [
  'en', 'pt', 'es', 'fr', 'de', 'it', 'ru', 'zh', 'ja', 'ko',
  'ar', 'hi', 'bn', 'ur', 'fa', 'tr', 'pl', 'nl', 'sv', 'no',
  'da', 'fi', 'cs', 'hu', 'ro', 'el', 'he', 'th', 'vi', 'id',
  'ms', 'tl', 'sw', 'am', 'yo', 'ig', 'ha', 'zu', 'xh', 'af',
  'sq', 'hy', 'az', 'eu', 'be', 'bg', 'ca', 'hr', 'et', 'gl',
  'ka', 'is', 'ga', 'lv', 'lt', 'mk', 'mt', 'sr', 'sk', 'sl',
  'uk', 'cy'
] as const;

export type SupportedLocale = typeof supportedLocales[number];

export const localeNames: Record<SupportedLocale, string> = {
  en: 'English', pt: 'Português', es: 'Español', fr: 'Français',
  de: 'Deutsch', it: 'Italiano', ru: 'Русский', zh: '中文',
  ja: '日本語', ko: '한국어', ar: 'العربية', hi: 'हिन्दी',
  bn: 'Bengali', ur: 'Urdu', fa: 'Persian', tr: 'Turkish', pl: 'Polish', nl: 'Dutch', sv: 'Swedish', no: 'Norwegian',
  da: 'Danish', fi: 'Finnish', cs: 'Czech', hu: 'Hungarian', ro: 'Romanian', el: 'Greek', he: 'Hebrew', th: 'Thai', vi: 'Vietnamese', id: 'Indonesian',
  ms: 'Malay', tl: 'Tagalog', sw: 'Swahili', am: 'Amharic', yo: 'Yoruba', ig: 'Igbo', ha: 'Hausa', zu: 'Zulu', xh: 'Xhosa', af: 'Afrikaans',
  sq: 'Albanian', hy: 'Armenian', az: 'Azerbaijani', eu: 'Basque', be: 'Belarusian', bg: 'Bulgarian', ca: 'Catalan', hr: 'Croatian', et: 'Estonian', gl: 'Galician',
  ka: 'Georgian', is: 'Icelandic', ga: 'Irish', lv: 'Latvian', lt: 'Lithuanian', mk: 'Macedonian', mt: 'Maltese', sr: 'Serbian', sk: 'Slovak', sl: 'Slovenian',
  uk: 'Ukrainian', cy: 'Welsh'
};

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

export const initI18n = async (defaultLocale: SupportedLocale = 'en'): Promise<void> => {
  await i18n
    .use(Backend)
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      fallbackLng: 'en',
      supportedLngs: supportedLocales as unknown as string[],
      load: 'languageOnly',
      interpolation: {
        escapeValue: false,
      },
      backend: {
        loadPath: '/locales/{{lng}}/common.json',
      },
      detection: {
        order: ['querystring', 'cookie', 'localStorage', 'navigator'],
        caches: ['localStorage', 'cookie'],
      },
      react: {
        useSuspense: false,
      },
    });

  // Configurar detecção automática de idioma com fallback
  const detected = i18n.language.split('-')[0] as SupportedLocale;
  const locale = (supportedLocales as readonly string[]).includes(detected) ? detected : defaultLocale;

  await i18n.changeLanguage(locale);
  await LocaleManager.setCurrentLocale(locale);

  // Carregar traduções automáticas para idiomas não suportados
  if (!(supportedLocales as readonly string[]).includes(detected)) {
    await TranslationService.loadAutoTranslations(detected);
  }
};

// ============================================================================
// HOOKS E UTILITÁRIOS
// ============================================================================

export const useArkheTranslation = () => {
  const { t, i18n } = useTranslation();

  const changeLocale = async (locale: SupportedLocale) => {
    if (!(supportedLocales as readonly string[]).includes(locale)) {
      // Idioma não suportado: usar tradução automática
      await TranslationService.enableAutoTranslation(locale);
    } else {
      await i18n.changeLanguage(locale);
      await LocaleManager.setCurrentLocale(locale);
    }
  };

  const getLocaleDirection = (): 'ltr' | 'rtl' => {
    const rtlLocales = ['ar', 'fa', 'he', 'ur'];
    return rtlLocales.includes(i18n.language) ? 'rtl' : 'ltr';
  };

  return {
    t,
    i18n,
    changeLocale,
    currentLocale: i18n.language as SupportedLocale,
    direction: getLocaleDirection(),
    isRTL: getLocaleDirection() === 'rtl',
  };
};

// ============================================================================
// TRADUÇÃO AUTOMÁTICA PARA DOMÍNIOS ESPECÍFICOS
// ============================================================================

export const translateDomainTerms = async (
  terms: string[],
  sourceLang: SupportedLocale,
  targetLang: SupportedLocale,
  domain: 'ethics' | 'technical' | 'legal' | 'general' = 'general'
): Promise<Record<string, string>> => {
  const translations: Record<string, string> = {};

  for (const term of terms) {
    // Tentar dicionário de domínio primeiro
    const domainDict = await LocaleManager.getDomainDictionary(domain, targetLang);
    if (domainDict[term]) {
      translations[term] = domainDict[term];
      continue;
    }

    // Fallback para tradução automática
    translations[term] = await TranslationService.translate(
      term,
      sourceLang,
      targetLang,
      { domain, context: 'arkhe_ethics' }
    );
  }

  return translations;
};

// ============================================================================
// COMPONENTES LOCALIZADOS
// ============================================================================

export const LocalizedText: React.FC<{
  text: string;
  domain?: 'ethics' | 'technical' | 'legal';
  style?: any;
}> = ({ text, domain = 'general', style }) => {
  const { t, i18n } = useTranslation();
  const [translated, setTranslated] = useState(text);

  useEffect(() => {
    const translate = async () => {
      const domainTerms = await translateDomainTerms(
        [text],
        'en' as SupportedLocale,
        i18n.language as SupportedLocale,
        domain as any
      );
      setTranslated(domainTerms[text] || text);
    };
    translate();
  }, [text, domain, i18n.language]);

  return <Text style={style}>{translated}</Text>;
};
