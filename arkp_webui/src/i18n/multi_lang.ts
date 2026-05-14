// ============================================================================
// multi_lang.ts — Suporte Multi-idioma para a Interface Web
// ============================================================================

export type LanguageCode = 'en' | 'pt' | 'es' | 'fr' | 'zh';

export interface TranslationDict {
  [key: string]: string | TranslationDict;
}

export const translations: Record<LanguageCode, TranslationDict> = {
  en: {
    dashboard: "Reputation Dashboard",
    voting: "Your Assessment",
    consensus: "Consensus Prediction",
    risk: "Risk Breakdown",
    submit: "Submit Vote"
  },
  pt: {
    dashboard: "Dashboard de Reputação",
    voting: "Sua Avaliação",
    consensus: "Previsão de Consenso",
    risk: "Análise de Risco",
    submit: "Enviar Voto"
  },
  es: {
    dashboard: "Panel de Reputación",
    voting: "Su Evaluación",
    consensus: "Predicción de Consenso",
    risk: "Análisis de Riesgo",
    submit: "Enviar Voto"
  },
  fr: {
    dashboard: "Tableau de Bord de Réputation",
    voting: "Votre Évaluation",
    consensus: "Prédiction de Consensus",
    risk: "Analyse des Risques",
    submit: "Soumettre le Vote"
  },
  zh: {
    dashboard: "声誉仪表板",
    voting: "您的评估",
    consensus: "共识预测",
    risk: "风险分析",
    submit: "提交投票"
  }
};

export class I18nManager {
  private currentLang: LanguageCode = 'en';

  constructor(defaultLang: LanguageCode = 'en') {
    this.currentLang = defaultLang;
  }

  setLanguage(lang: LanguageCode) {
    if (translations[lang]) {
      this.currentLang = lang;
    }
  }

  t(key: string): string {
    const parts = key.split('.');
    let current: any = translations[this.currentLang];

    for (const part of parts) {
      if (current[part] === undefined) {
        return key; // Fallback
      }
      current = current[part];
    }

    return typeof current === 'string' ? current : key;
  }
}
