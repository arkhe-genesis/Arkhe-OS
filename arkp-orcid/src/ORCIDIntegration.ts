// ============================================================================
// ORCIDIntegration — Integração completa com ORCID API para perfis acadêmicos
// Substrato 9004: Perfil acadêmico rico para cálculo de reputação
// ============================================================================

import { ReviewerIdentity, AcademicProfile, Publication, Affiliation } from './types';
import { QIPEngine } from '../qip/QIPEngine';

export class ORCIDIntegration {
  private static readonly API_BASE = 'https://pub.orcid.org/v3.0';
  private static readonly SANDBOX_BASE = 'https://sandbox.orcid.org/v3.0';
  private static readonly SCOPES = [
    '/read-limited',
    '/activities/update',
    '/person/update',
    '/openid',
  ].join(' ');

  constructor(
    private clientId: string,
    private clientSecret: string,
    private redirectUri: string,
    private sandbox: boolean = false
  ) {}

  /**
   * Inicia fluxo OAuth2 com ORCID
   */
  getAuthorizationUrl(state: string, scopes?: string[]): string {
    const baseUrl = this.sandbox ? ORCIDIntegration.SANDBOX_BASE : ORCIDIntegration.API_BASE;
    const scope = scopes?.join(' ') || ORCIDIntegration.SCOPES;

    const params = new URLSearchParams({
      client_id: this.clientId,
      response_type: 'code',
      scope,
      redirect_uri: this.redirectUri,
      state,
    });

    return `${baseUrl}/oauth/authorize?${params.toString()}`;
  }

  /**
   * Troca código de autorização por token de acesso
   */
  async exchangeCode(code: string): Promise<{
    accessToken: string;
    refreshToken: string;
    orcid: string;
    name: string;
  }> {
    const baseUrl = this.sandbox ? ORCIDIntegration.SANDBOX_BASE : ORCIDIntegration.API_BASE;

    const response = await fetch(`${baseUrl}/oauth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      },
      body: new URLSearchParams({
        client_id: this.clientId,
        client_secret: this.clientSecret,
        grant_type: 'authorization_code',
        code,
        redirect_uri: this.redirectUri,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`ORCID token exchange failed: ${error}`);
    }

    const tokenData = await response.json();

    // Obter perfil básico com o token
    const profile = await this.fetchProfile(tokenData.access_token);

    return {
      accessToken: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
      orcid: profile.orcid,
      name: profile.name,
    };
  }

  /**
   * Busca perfil completo do pesquisador
   */
  async fetchProfile(accessToken: string): Promise<AcademicProfile> {
    const baseUrl = this.sandbox ? ORCIDIntegration.SANDBOX_BASE : ORCIDIntegration.API_BASE;

    // Buscar informações pessoais
    const personResponse = await fetch(`${baseUrl}/person`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json',
      },
    });

    if (!personResponse.ok) {
      throw new Error('Failed to fetch ORCID person data');
    }

    const personData = await personResponse.json();

    // Buscar atividades (publicações, afiliações, etc.)
    const activitiesResponse = await fetch(`${baseUrl}/${personData['orcid-identifier'].path}/activities`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json',
      },
    });

    const activitiesData = activitiesResponse.ok ? await activitiesResponse.json() : null;

    // Construir perfil acadêmico rico
    return {
      orcid: personData['orcid-identifier'].path,
      name: this.extractName(personData),
      emails: this.extractEmails(personData),
      keywords: this.extractKeywords(personData),
      publications: await this.fetchPublications(accessToken, personData['orcid-identifier'].path),
      affiliations: this.extractAffiliations(personData, activitiesData),
      citations: await this.fetchCitationMetrics(personData['orcid-identifier'].path),
      hIndex: await this.fetchHIndex(personData['orcid-identifier'].path),
      lastUpdated: new Date().toISOString(),
    };
  }

  /**
   * Calcula reputação acadêmica baseada no perfil ORCID
   */
  async calculateAcademicReputation(profile: AcademicProfile): Promise<number> {
    let score = 0.0;

    // Fator 1: Volume de publicações (log scale)
    const pubCount = profile.publications?.length || 0;
    const pubScore = Math.min(1.0, Math.log10(Math.max(1, pubCount)) / 3);
    score += pubScore * 0.30;

    // Fator 2: Impacto (citações e h-index)
    const citationScore = Math.min(1.0, (profile.citations?.total || 0) / 1000);
    const hIndexScore = Math.min(1.0, (profile.hIndex || 0) / 30);
    score += (citationScore * 0.25 + hIndexScore * 0.15) * 0.40;

    // Fator 3: Diversidade de afiliações
    const affiliationScore = Math.min(1.0, (profile.affiliations?.length || 0) / 3);
    score += affiliationScore * 0.15;

    // Fator 4: Atividade recente (últimos 2 anos)
    const recentPubs = profile.publications?.filter(
      p => new Date(p.publicationDate).getFullYear() >= new Date().getFullYear() - 2
    ).length || 0;
    const recencyScore = Math.min(1.0, recentPubs / 5);
    score += recencyScore * 0.15;

    // Fator 5: Colaboração internacional
    const intlAffiliations = profile.affiliations?.filter(
      a => a.country && a.country !== profile.primaryCountry
    ).length || 0;
    const collaborationBonus = Math.min(0.1, intlAffiliations * 0.02);
    score += collaborationBonus;

    return Math.min(1.0, Math.max(0.0, score));
  }

  /**
   * Integra perfil ORCID com sistema QIP de reputação
   */
  async integrateWithQIP(
    orcid: string,
    accessToken: string,
    qipEngine: QIPEngine
  ): Promise<{
    academicReputation: number;
    qipBonus: number;
    totalReputation: number;
  }> {
    // Buscar perfil acadêmico
    const profile = await this.fetchProfile(accessToken);

    // Calcular reputação acadêmica
    const academicReputation = await this.calculateAcademicReputation(profile);

    // Calcular bônus QIP baseado em métricas acadêmicas
    const qipBonus = this.calculateQIPBonus(profile, academicReputation);

    // Atualizar reputação no QIP Engine
    await qipEngine.updateReviewerReputation(orcid, {
      academicReputation,
      qipBonus,
      profile,
      lastSync: new Date().toISOString(),
    });

    return {
      academicReputation,
      qipBonus,
      totalReputation: Math.min(1.0, academicReputation + qipBonus),
    };
  }

  /**
   * Calcula bônus QIP baseado em métricas acadêmicas
   */
  private calculateQIPBonus(profile: AcademicProfile, academicReputation: number): number {
    let bonus = 0.0;

    // Bônus por publicações de alto impacto
    const highImpactPubs = profile.publications?.filter(
      p => (p.citationCount || 0) > 100 || (p.journal?.impactFactor && p.journal.impactFactor > 10)
    ).length || 0;
    bonus += Math.min(0.10, highImpactPubs * 0.02);

    // Bônus por afiliações em instituições de elite
    const eliteInstitutions = ['Harvard', 'MIT', 'Stanford', 'Oxford', 'Cambridge', 'Max Planck'];
    const eliteAffiliations = profile.affiliations?.filter(
      a => eliteInstitutions.some(elite => a.organization?.toLowerCase().includes(elite.toLowerCase()))
    ).length || 0;
    bonus += Math.min(0.05, eliteAffiliations * 0.01);

    // Bônus por colaboração com a Catedral (publicações com co-autores ARKHE)
    const arkheCollabs = profile.publications?.filter(
      p => p.authors?.some(a => a.orcid?.startsWith('ARKHE-'))
    ).length || 0;
    bonus += Math.min(0.10, arkheCollabs * 0.03);

    // Bônus por atividade em domínios relevantes
    const relevantKeywords = ['ai ethics', 'ai safety', 'formal verification', 'temporal logic'];
    const keywordMatches = profile.keywords?.filter(
      k => relevantKeywords.some(rk => k.toLowerCase().includes(rk.toLowerCase()))
    ).length || 0;
    bonus += Math.min(0.05, keywordMatches * 0.01);

    return Math.min(0.30, bonus); // Limite de 30% de bônus
  }

  // Métodos auxiliares para parsing de dados ORCID...
  private extractName(personData: any): string {
    const creditName = personData['name']?.['credit-name']?.value;
    if (creditName) return creditName;

    const given = personData['name']?.['given-names']?.value || '';
    const family = personData['name']?.['family-name']?.value || '';
    return [given, family].filter(Boolean).join(' ').trim() || 'Unknown';
  }

  private extractEmails(personData: any): string[] {
    return personData['emails']?.['email']
      ?.filter((e: any) => e['primary'] === 'true' || e['verified'] === 'true')
      .map((e: any) => e['email']) || [];
  }

  private extractKeywords(personData: any): string[] {
    return personData['keywords']?.['keyword']?.map((k: any) => k.content) || [];
  }

  private extractAffiliations(personData: any, activitiesData: any): Affiliation[] {
    // Extrair afiliações de empregador e educação
    const affiliations: Affiliation[] = [];

    // Empregadores
    const employments = activitiesData?.['employments']?.['affiliation-group'] || [];
    for (const group of employments) {
      const summaries = group['summaries'] || [];
      for (const summary of summaries) {
        const affiliation = summary['employment-summary'];
        affiliations.push({
          organization: affiliation?.['organization']?.['name']?.value,
          department: affiliation?.['department-name']?.value,
          role: affiliation?.['role-title']?.value,
          startDate: affiliation?.['start-date']?.value,
          endDate: affiliation?.['end-date']?.value,
          country: affiliation?.['organization']?.['address']?.['country'],
          type: 'employment',
        });
      }
    }

    // Educação
    const educations = activitiesData?.['educations']?.['affiliation-group'] || [];
    for (const group of educations) {
      const summaries = group['summaries'] || [];
      for (const summary of summaries) {
        const education = summary['education-summary'];
        affiliations.push({
          organization: education?.['organization']?.['name']?.value,
          department: education?.['department-name']?.value,
          role: education?.['role-title']?.value,
          startDate: education?.['start-date']?.value,
          endDate: education?.['end-date']?.value,
          country: education?.['organization']?.['address']?.['country'],
          type: 'education',
        });
      }
    }

    return affiliations.filter(a => a.organization);
  }

  private async fetchPublications(accessToken: string, orcid: string): Promise<Publication[]> {
    // Implementação simplificada - em produção, buscar works do ORCID
    const baseUrl = this.sandbox ? ORCIDIntegration.SANDBOX_BASE : ORCIDIntegration.API_BASE;

    try {
      const response = await fetch(`${baseUrl}/${orcid}/works`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json',
        },
      });

      if (!response.ok) return [];

      const worksData = await response.json();
      // Parse e mapear para formato Publication...
      return []; // Placeholder
    } catch {
      return [];
    }
  }

  private async fetchCitationMetrics(orcid: string): Promise<{ total: number; byYear: Record<number, number>, byPublication: Record<string, number> }> {
    // Integração com APIs de métricas (Crossref, Dimensions, etc.)
    // Placeholder para implementação futura
    return { total: 0, byYear: {}, byPublication: {} };
  }

  private async fetchHIndex(orcid: string): Promise<number | undefined> {
    // Calcular h-index a partir das publicações
    // Placeholder para implementação futura
    return undefined;
  }
}
