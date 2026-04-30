
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, no-shadow-restricted-names */


import React, { useState, useEffect } from 'react';

import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Label } from './ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select';
import { Switch } from './ui/Switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs';

interface PrivacyProfile {
  citizenId: string;
  profile: 'CONSERVATIVE' | 'BALANCED' | 'OPEN';
  consents: Record<string, boolean>;
}

const CitizenPortal: React.FC = () => {
  const [profile, setProfile] = useState<PrivacyProfile>({
    citizenId: 'cit_user_01',
    profile: 'BALANCED',
    consents: {
      analytics: true,
      personalization: true,
      data_sharing: false,
    },
  });

  const [explanations, setExplanations] = useState<any[]>([]);

  useEffect(() => {
    // Mocking initial explanations based on profile
    const mockExplanations = [
      {
        id: 'dec_001',
        title: 'Proteção de Identidade',
        date: '2026-04-24 14:20',
        summary: profile.profile === 'CONSERVATIVE'
          ? 'Uma ação foi tomada para proteger seus dados.'
          : 'Detectamos um risco de vazamento e isolamos seus dados pessoais preventivamente.',
        persona: profile.profile === 'OPEN' ? 'TECHNICAL' : 'CITIZEN',
      },
      {
        id: 'dec_002',
        title: 'Otimização de Recurso',
        date: '2026-04-24 10:15',
        summary: 'Carga de processamento redistribuída para garantir estabilidade.',
        persona: 'CITIZEN',
      }
    ];
    setExplanations(mockExplanations);
  }, [profile]);

  const updateProfile = (newProfile: 'CONSERVATIVE' | 'BALANCED' | 'OPEN') => {
    setProfile(prev => ({ ...prev, profile: newProfile }));
  };

  const toggleConsent = (key: string) => {
    setProfile(prev => ({
      ...prev,
      consents: { ...prev.consents, [key]: !prev.consents[key] }
    }));
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-2">
            🛡️ Portal do Cidadão Arkhe
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="profile">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="profile">Configurações de Privacidade</TabsTrigger>
              <TabsTrigger value="explanations">Minhas Explicações</TabsTrigger>
            </TabsList>

            <TabsContent value="profile" className="space-y-6 mt-4">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Perfil de Privacidade</Label>
                  <Select
                    data-value={profile.profile}
                    onValueChange={(val: any) => updateProfile(val)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um perfil" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CONSERVATIVE">Conservador (Máxima Proteção)</SelectItem>
                      <SelectItem value="BALANCED">Equilibrado (Recomendado)</SelectItem>
                      <SelectItem value="OPEN">Aberto (Personalização Máxima)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-muted-foreground italic">
                    {profile.profile === 'CONSERVATIVE' && "Privacidade Total: Seus dados são usados apenas para o estritamente necessário."}
                    {profile.profile === 'BALANCED' && "Uso Equilibrado: Transparência e melhoria contínua dos serviços."}
                    {profile.profile === 'OPEN' && "Experiência Personalizada: Otimização total da sua interação com a Catedral."}
                  </p>
                </div>

                <div className="space-y-4 border-t pt-4">
                  <Label className="text-lg font-semibold">Consentimentos Dinâmicos</Label>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Análise de Comportamento</Label>
                      <p className="text-sm text-muted-foreground">Permite o uso de dados anônimos para melhorar o sistema.</p>
                    </div>
                    <Switch
                      checked={profile.consents.analytics}
                      onCheckedChange={() => toggleConsent('analytics')}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Personalização de Explicação</Label>
                      <p className="text-sm text-muted-foreground">Adapta o diálogo ao seu contexto cultural.</p>
                    </div>
                    <Switch
                      checked={profile.consents.personalization}
                      onCheckedChange={() => toggleConsent('personalization')}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Compartilhamento com Reguladores</Label>
                      <p className="text-sm text-muted-foreground">Facilita auditorias externas em seu nome.</p>
                    </div>
                    <Switch
                      checked={profile.consents.data_sharing}
                      onCheckedChange={() => toggleConsent('data_sharing')}
                    />
                  </div>
                </div>

                <div className="space-y-4 border-t pt-4">
                  <Label className="text-lg font-semibold text-red-500">Zona de Perigo</Label>
                  <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
                    <h5 className="font-bold text-red-700">Crypto-Shredding (Exclusão Total)</h5>
                    <p className="text-sm text-red-600 mb-4">
                      Ao ativar esta opção, as chaves de criptografia vinculadas aos seus dados serão destruídas permanentemente.
                      Isso torna todo o seu histórico ilegível e irrecuperável, cumprindo o Direito ao Esquecimento.
                    </p>
                    <Button variant="destructive" size="sm">
                      Destruir Minhas Chaves de Dados
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="explanations" className="space-y-4 mt-4">
              {explanations.map(exp => (
                <Card key={exp.id} className="border-l-4 border-l-blue-500">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-bold text-lg">{exp.title}</h4>
                        <span className="text-xs text-muted-foreground">{exp.date}</span>
                      </div>
                      <Badge variant="outline">{exp.persona}</Badge>
                    </div>
                    <p className="text-sm">{exp.summary}</p>
                    <Button variant="link" className="p-0 h-auto mt-2 text-blue-500">
                      Ver detalhes técnicos
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default CitizenPortal;
