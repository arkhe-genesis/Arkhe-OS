// ============================================================================
// Tipos para Integração ORCID
// ============================================================================

export interface AcademicProfile {
  orcid: string;
  name: string;
  emails: string[];
  keywords: string[];
  publications: Publication[];
  affiliations: Affiliation[];
  citations?: {
    total: number;
    byYear: Record<number, number>;
    byPublication: Record<string, number>;
  };
  hIndex?: number;
  primaryCountry?: string;
  lastUpdated: string;
}

export interface Publication {
  title: string;
  authors: Array<{
    name: string;
    orcid?: string;
    affiliation?: string;
  }>;
  publicationDate: string;
  journal?: {
    name: string;
    impactFactor?: number;
    publisher?: string;
  };
  doi?: string;
  citationCount?: number;
  openAccess?: boolean;
  arkheRelated?: boolean; // Se menciona ARKHE ou substratos
}

export interface Affiliation {
  organization: string;
  department?: string;
  role?: string;
  startDate?: string;
  endDate?: string;
  country?: string;
  type: 'employment' | 'education' | 'funding' | 'other';
}

export interface QIPAcademicUpdate {
  academicReputation: number;
  qipBonus: number;
  profile: AcademicProfile;
  lastSync: string;
  syncSource: 'orcid' | 'manual' | 'auto';
}
export type ReviewerIdentity = any;
