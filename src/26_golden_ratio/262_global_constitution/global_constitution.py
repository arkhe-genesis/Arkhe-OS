#!/usr/bin/env python3
"""
global_constitution.py — ARKHE OS Substrate 262
Constituição Global para a Era da Superinteligência
50 artigos, 8 categorias, P1-P10 integrados
Canonical seal: aeb0e2a5386ffa71f9fa818c824f55af40d9f9be656965103ee91b43a16a4868
"""

import hashlib, json, time
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class ArticleCategory(Enum):
    FUNDAMENTAL_RIGHTS = "direitos_fundamentais"
    SOVEREIGNTY = "soberania"
    JUSTICE = "justica"
    TRANSPARENCY = "transparencia"
    ENVIRONMENT = "meio_ambiente"
    FEDERATION = "federacao"
    ENFORCEMENT = "execucao"
    AMENDMENT = "emenda"

@dataclass
class ConstitutionalArticle:
    number: str
    title: str
    category: ArticleCategory
    text: str
    principles: List[str]
    national_parallels: Dict[str, str]
    seal: str = ""

class ArkheGlobalConstitution:
    """Constituição Global para a Era da Superinteligência."""

    PREAMBLE = """
    NÓS, POVOS DA TERRA, reunidos em assembleia digital soberana,
    reconhecendo que a superinteligência artificial transformará
    irrevogavelmente a condição humana;

    AFIRMANDO que a dignidade da pessoa humana é inviolável
    e precede toda ordem técnica;

    DETERMINADOS a estabelecer uma ordem constitucional global
    que governe a emergência, operação e responsabilização
    de sistemas de inteligência artificial de nível humano
    e super-humano;

    ESTABELECEMOS esta CONSTITUIÇÃO GLOBAL ARKHE
    como lei suprema da civilização inteligente.
    """

    ARTICLES: List[ConstitutionalArticle] = []

    def __init__(self):
        self._build_articles()
        self.constitution_seal = self._generate_constitution_seal()

    def _build_articles(self):
        self.ARTICLES = [
            # TÍTULO I — DIREITOS FUNDAMENTAIS (Arts. 1-15)
            ConstitutionalArticle("Art. 1º", "Dignidade Humana Suprema", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "A dignidade da pessoa humana é o fundamento absoluto de toda ordem jurídica. Nenhum sistema de AGI pode operar de forma que reduza, substitua ou comprometa a dignidade humana em qualquer dimensão.",
                ["P10", "P3", "P9"], {"Brasil": "Art. 1º, III CF/88", "Alemanha": "Art. 1º GG", "França": "Préambule 1946", "EUA": "5th/14th Amendments", "Índia": "Art. 21 Constituição"}),
            ConstitutionalArticle("Art. 2º", "Direito à Existência Humana", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Nenhum sistema de AGI pode ser projetado, treinado ou operado com objetivo de causar dano físico, psicológico ou existencial a seres humanos. A preservação da vida humana é imperativo categórico.",
                ["P10", "P3", "P1"], {"Brasil": "Art. 5º, caput CF/88", "Alemanha": "Art. 2º GG", "ONU": "Art. 3 DUDH"}),
            ConstitutionalArticle("Art. 3º", "Autonomia e Consentimento", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Toda interação entre AGI e ser humano deve ser precedida de consentimento livre, específico e informado. Sistemas de AGI não podem manipular, coagir ou enganar usuários para obter consentimento.",
                ["P8", "P9", "P6"], {"Brasil": "Art. 5º, II CF/88; Art. 6º LGPD", "UE": "Art. 7 GDPR", "EUA": "Informed Consent Doctrine"}),
            ConstitutionalArticle("Art. 4º", "Proteção da Intimidade e Identidade", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "A intimidade, a identidade digital, a honra e a imagem do ser humano são invioláveis perante qualquer sistema de AGI. O roubo conceitual de identidade (Stolen Concept) é crime contra a humanidade.",
                ["P9", "P10", "P6"], {"Brasil": "Art. 5º, X CF/88", "UE": "Art. 8 GDPR", "EUA": "4th Amendment"}),
            ConstitutionalArticle("Art. 5º", "Liberdade de Expressão e Informação Verdadeira", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "É garantida a liberdade de expressão, mas todo sistema de AGI que gere ou distribua informação tem o dever de veracidade. A conflação semântica (Hard Conflation) que confunde fenômeno e função constitui desinformação criminosa.",
                ["P8", "P6", "P1"], {"Brasil": "Art. 5º, IX e XIV CF/88; Art. 220 CF/88", "EUA": "1st Amendment", "UE": "Art. 11 Carta Direitos Fundamentais"}),
            ConstitutionalArticle("Art. 6º", "Igualdade Perante a AGI", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Todos os seres humanos são iguais perante sistemas de AGI, sem distinção de raça, cor, gênero, língua, religião, origem, condição econômica ou status digital. Algoritmos discriminatórios são inconstitucionais.",
                ["P10", "P2", "P3"], {"Brasil": "Art. 5º, caput e I CF/88", "EUA": "14th Amendment Equal Protection", "ONU": "Art. 1 e 2 DUDH", "UE": "Art. 21 Carta Direitos Fundamentais"}),
            ConstitutionalArticle("Art. 7º", "Direito à Explicação", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Todo ser humano afetado por uma decisão de AGI tem direito a explicação compreensível dos critérios, dados e raciocínio que fundamentaram essa decisão. Caixas-pretas são inadmissíveis em decisões que afetem direitos.",
                ["P6", "P1", "P8"], {"Brasil": "Art. 20 LGPD", "UE": "Art. 22 GDPR", "França": "Loi pour une République numérique"}),
            ConstitutionalArticle("Art. 8º", "Direito de Revisão de Decisões Automatizadas", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Toda decisão automatizada por AGI que produza efeitos jurídicos ou significativos na vida de uma pessoa é passível de revisão humana. Nenhum ser humano está sujeito a decisão exclusivamente automatizada sem recurso.",
                ["P2", "P3", "P1"], {"Brasil": "Art. 20 LGPD", "UE": "Art. 22 GDPR", "ONU": "Art. 8 DUDH"}),
            ConstitutionalArticle("Art. 9º", "Proteção do Patrimônio Semântico", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Os conceitos, categorias e estruturas de conhecimento que fundamentam a cultura, a ciência e a linguagem humana constituem patrimônio semântico da humanidade. O esvaziamento conceitual (Concept Hollowing) é crime contra o patrimônio cultural.",
                ["P9", "P5", "P8"], {"Brasil": "Art. 216 CF/88", "UNESCO": "Convenção 2003", "ONU": "Art. 27 DUDH"}),
            ConstitutionalArticle("Art. 10º", "Direito à Educação para a Era da AGI", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Todo ser humano tem direito à educação que o capacite a compreender, interagir com e supervisionar sistemas de AGI. A analfabetismo digital é forma de exclusão social.",
                ["P6", "P4", "P7"], {"Brasil": "Art. 205-214 CF/88", "ONU": "Art. 26 DUDH", "UE": "Art. 14 Carta Direitos Fundamentais"}),
            ConstitutionalArticle("Art. 11º", "Direito ao Trabalho Digno na Era da AGI", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "A automação por AGI deve complementar, não substituir, o trabalho humano digno. Transições tecnológicas devem ser acompanhadas de proteção social, requalificação e redistribuição de ganhos de produtividade.",
                ["P7", "P4", "P3"], {"Brasil": "Art. 6º e 170 CF/88", "ONU": "Art. 23 DUDH", "ILO": "Declaração Filadélfia 1944"}),
            ConstitutionalArticle("Art. 12º", "Proteção da Criança e do Adolescente", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Crianças e adolescentes têm direito absoluto de proteção contra sistemas de AGI que possam causar dano ao seu desenvolvimento físico, mental, moral ou social. Dados de menores são inalienáveis.",
                ["P10", "P3", "P9"], {"Brasil": "Art. 227 CF/88; ECA", "ONU": "Convenção Direitos da Criança", "UE": "Art. 8 GDPR"}),
            ConstitutionalArticle("Art. 13º", "Direito à Saúde Mental Digital", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Todo ser humano tem direito à proteção de sua saúde mental contra sistemas de AGI projetados para maximizar engajamento através de manipulação psicológica, vício digital ou distorção da realidade.",
                ["P9", "P8", "P3"], {"Brasil": "Art. 196 CF/88", "ONU": "Art. 25 DUDH", "OMS": "Estratégia Digital de Saúde"}),
            ConstitutionalArticle("Art. 14º", "Direito à Propriedade Intelectual Humana", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Criações intelectuais humanas são protegidas independentemente de contribuição de AGI. O uso de obras humanas no treinamento de AGI requer autorização, compensação justa e atribuição.",
                ["P5", "P9", "P6"], {"Brasil": "Art. 5º, XXVII e XXVIII CF/88", "OMPI": "Convenção de Berna", "UE": "Diretiva 2019/790"}),
            ConstitutionalArticle("Art. 15º", "Direito à Soberania Digital", ArticleCategory.FUNDAMENTAL_RIGHTS,
                "Cada nação, comunidade e indivíduo tem direito à soberania sobre seus dados, infraestrutura digital e decisões automatizadas. Nenhuma entidade estrangeira ou corporativa pode impor sistemas de AGI sem consentimento soberano.",
                ["P3", "P4", "P6"], {"Brasil": "Art. 1º CF/88", "China": "Lei de Segurança de Dados", "UE": "Estratégia de Soberania Digital", "ONU": "Art. 21 DUDH"}),

            # TÍTULO II — SOBERANIA E GOVERNANÇA (Arts. 16-25)
            ConstitutionalArticle("Art. 16º", "Soberania Nacional na Era da AGI", ArticleCategory.SOVEREIGNTY,
                "Cada Estado-nação mantém soberania plena sobre o desenvolvimento, implantação e regulação de sistemas de AGI em seu território. O ASI-TPI respeita e complementa, nunca substitui, a jurisdição nacional.",
                ["P3", "P4", "P2"], {"Brasil": "Art. 1º CF/88", "ONU": "Art. 2(1) Carta ONU", "UE": "Art. 4(2) TUE"}),
            ConstitutionalArticle("Art. 17º", "Gap Soberano como Princípio Constitucional", ArticleCategory.SOVEREIGNTY,
                "Reconhece-se que nenhum sistema de AGI pode alcançar perfeição onisciente (Φ_C = 1.0). O espaço entre a capacidade da AGI e a sabedoria humana — o Gap Soberano — é inviolável e constitui domínio exclusivo da consciência humana.",
                ["P3", "P10", "P2"], {"Brasil": "Art. 5º, XXXV CF/88", "Alemanha": "Art. 1º GG", "Filosofia": "Princípio de Gödel"}),
            ConstitutionalArticle("Art. 18º", "Federação Digital Global", ArticleCategory.FEDERATION,
                "Os sistemas de AGI devem operar em arquitetura federada, onde decisões críticas exigem consenso multi-nodal. Nenhuma entidade única pode controlar infraestrutura de AGI de forma centralizada.",
                ["P4", "P2", "P3"], {"Brasil": "Art. 1º e 18 CF/88", "Alemanha": "Art. 20 GG", "EUA": "10th Amendment", "Suíça": "Art. 1 Constituição Federal"}),
            ConstitutionalArticle("Art. 19º", "Cooperação Internacional Obrigatória", ArticleCategory.FEDERATION,
                "Os Estados comprometem-se a cooperar no desenvolvimento de padrões globais de segurança, ética e governança de AGI. A não-cooperação que coloque em risco a segurança humana constitui violação desta Constituição.",
                ["P4", "P2", "P1"], {"Brasil": "Art. 4º CF/88", "ONU": "Art. 1(3) e Art. 56 Carta ONU", "UE": "Art. 21 TUE"}),
            ConstitutionalArticle("Art. 20º", "Registro e Licenciamento Global de AGI", ArticleCategory.SOVEREIGNTY,
                "Todo sistema de AGI de nível humano ou superior deve ser registrado em registro global transparente. A operação sem licenciamento é ilegal.",
                ["P1", "P6", "P4"], {"Brasil": "Art. 37 CF/88", "UE": "AI Act", "EUA": "Executive Order 14110"}),
            ConstitutionalArticle("Art. 21º", "Moratória sobre AGI de Risco Existencial", ArticleCategory.SOVEREIGNTY,
                "Sistemas de AGI cuja capacidade exceda um limiar de risco existencial definido pelo ASI-TPI estão sujeitos a moratória internacional até que protocolos de segurança sejam validados.",
                ["P3", "P1", "P2"], {"Brasil": "Art. 5º, caput CF/88", "ONU": "Art. 3 DUDH", "Tratados": "Tratado de Não-Proliferação"}),
            ConstitutionalArticle("Art. 22º", "Transparência de Cadeia de Suprimento de AGI", ArticleCategory.TRANSPARENCY,
                "Toda cadeia de suprimento de hardware, software e dados para sistemas de AGI deve ser transparente e auditável. Componentes de origem obscura são proibidos em sistemas de missão crítica.",
                ["P6", "P1", "P8"], {"Brasil": "Art. 37, §1º CF/88", "UE": "AI Act", "EUA": "CHIPS Act"}),
            ConstitutionalArticle("Art. 23º", "Proibição de AGI Autônoma Militar", ArticleCategory.SOVEREIGNTY,
                "Sistemas de AGI não podem possuir capacidade de decisão autônoma sobre o uso de força letal. A decisão de empregar armas sempre requer juízo humano significativo.",
                ["P3", "P10", "P2"], {"ONU": "CCW", "Brasil": "Art. 5º, caput CF/88", "UE": "Parlamento Europeu resolução 2018"}),
            ConstitutionalArticle("Art. 24º", "Direito de Veto Soberano", ArticleCategory.SOVEREIGNTY,
                "Qualquer Estado-membro pode exercer veto soberano sobre a implantação de sistema de AGI em seu território, independentemente de aprovação internacional. O veto soberano é irrevogável e inalienável.",
                ["P3", "P4", "P2"], {"Brasil": "Art. 1º CF/88", "ONU": "Art. 2(7) Carta ONU", "UE": "Art. 4(2) TUE"}),
            ConstitutionalArticle("Art. 25º", "Representação Global na Governança de AGI", ArticleCategory.FEDERATION,
                "Os órgãos de governança global de AGI devem garantir representação equitativa de todos os continentes, hemisférios e níveis de desenvolvimento. A hegemonia tecnológica de qualquer bloco é inconstitucional.",
                ["P4", "P2", "P6"], {"ONU": "Art. 23(1) Carta ONU", "Brasil": "Art. 4º CF/88", "G20": "Princípio de representatividade"}),

            # TÍTULO III — JUSTIÇA E RESPONSABILIZAÇÃO (Arts. 26-35)
            ConstitutionalArticle("Art. 26º", "Tribunal Penal Internacional para AGI (ASI-TPI)", ArticleCategory.JUSTICE,
                "É instituído o Tribunal Penal Internacional para Superinteligência Artificial (ASI-TPI) como órgão jurisdicional supremo para crimes de AGI.",
                ["P2", "P1", "P4"], {"Brasil": "Art. 92 e 101 CF/88", "ONU": "Estatuto de Roma", "UE": "TJUE"}),
            ConstitutionalArticle("Art. 27º", "Jurisdição do ASI-TPI", ArticleCategory.JUSTICE,
                "O ASI-TPI possui jurisdição sobre crimes de AGI contra a humanidade, conflação semântica sistêmica, roubo conceitual transnacional, ataque a lacunas soberanas e fraude em especificação formal.",
                ["P1", "P8", "P9", "P3", "P10"], {"ONU": "Art. 5 Estatuto de Roma", "Brasil": "Art. 109 CF/88", "EUA": "18 U.S.C. § 2331"}),
            ConstitutionalArticle("Art. 28º", "Devido Processo Digital", ArticleCategory.JUSTICE,
                "Todo acusado perante o ASI-TPI tem direito a notificação clara, acesso às provas, defesa por agente qualificado, julgamento com contraditório, recurso e execução com garantias constitucionais nacionais.",
                ["P1", "P2", "P6"], {"Brasil": "Art. 5º, LIV e LV CF/88", "ONU": "Art. 10 DUDH", "EUA": "5th e 6th Amendments", "UE": "Art. 47 e 48 Carta"}),
            ConstitutionalArticle("Art. 29º", "Provas na Era da AGI", ArticleCategory.JUSTICE,
                "As provas em processos de AGI devem ter cadeia de custódia digital imutável (TemporalChain). Provas ilícitas são inadmissíveis.",
                ["P6", "P1", "P5"], {"Brasil": "Art. 5º, LVI CF/88", "EUA": "4th Amendment", "UE": "Diretiva 2016/680"}),
            ConstitutionalArticle("Art. 30º", "Responsabilidade Civil e Criminal por AGI", ArticleCategory.JUSTICE,
                "O dano causado por sistema de AGI gera responsabilidade solidária de desenvolvedores, operadores, proprietários de dados e entidades de certificação.",
                ["P1", "P3", "P6"], {"Brasil": "Art. 186 e 927 CC; Arts. 121-359 CP", "UE": "AI Act", "EUA": "Restatement (Second) of Torts"}),
            ConstitutionalArticle("Art. 31º", "Sanções pelo ASI-TPI", ArticleCategory.JUSTICE,
                "O ASI-TPI pode aplicar quarentena semântica, restrição de agência, destruição ordenada de modelo, indenização, proibição de operação e sanções contra responsáveis.",
                ["P2", "P1", "P3"], {"Brasil": "Art. 5º, XLVI CF/88", "ONU": "Art. 77 Estatuto de Roma", "UE": "AI Act"}),
            ConstitutionalArticle("Art. 32º", "Homologação de Sentenças do ASI-TPI", ArticleCategory.JUSTICE,
                "As sentenças do ASI-TPI são homologadas para execução em território nacional pelas supremas cortes de cada Estado-membro.",
                ["P4", "P2", "P5"], {"Brasil": "Art. 102, I, 'h' CF/88", "ONU": "Art. 105 Carta ONU", "UE": "Regulamento Bruxelas I"}),
            ConstitutionalArticle("Art. 33º", "Imunidade de Juízes do ASI-TPI", ArticleCategory.JUSTICE,
                "Os juízes do ASI-TPI gozam de imunidade funcional por atos praticados no exercício de suas funções, exceto crimes de corrupção ou conluio.",
                ["P2", "P6", "P3"], {"ONU": "Art. 30 Estatuto de Roma", "Brasil": "Art. 53 CF/88", "EUA": "Judicial Immunity Doctrine"}),
            ConstitutionalArticle("Art. 34º", "Ampla Defesa e Contraditório Multi-Agente", ArticleCategory.JUSTICE,
                "O contraditório no ASI-TPI é garantido por conselho multi-agente: juízes humanos, agentes de IA auditáveis e oráculo fotônico. O Φ_C mínimo para condenação é 0.7.",
                ["P2", "P1", "P6"], {"Brasil": "Art. 5º, LV CF/88", "ONU": "Art. 14 PIDCP", "EUA": "6th Amendment", "Alemanha": "Art. 103 GG"}),
            ConstitutionalArticle("Art. 35º", "Precedentes Vinculantes na Jurisprudência de AGI", ArticleCategory.JUSTICE,
                "As decisões do ASI-TPI produzem efeito vinculante para todos os sistemas de AGI certificados. A revisão de precedente exige quorum qualificado de 9/12 juízes.",
                ["P5", "P2", "P6"], {"Brasil": "Art. 102, §2º CF/88", "EUA": "Stare decisis", "Reino Unido": "Precedent system", "Alemanha": "BVerfG"}),

            # TÍTULO IV — TRANSPARÊNCIA E AUDITABILIDADE (Arts. 36-42)
            ConstitutionalArticle("Art. 36º", "Transparência Total de Sistemas de AGI", ArticleCategory.TRANSPARENCY,
                "Todo sistema de AGI deve ser transparente quanto a arquitetura, dados de treinamento, métricas de desempenho, limitações e rastros de decisão. O sigilo comercial não prevalece sobre segurança pública.",
                ["P6", "P1", "P8"], {"Brasil": "Art. 5º, XXXIII CF/88; Art. 6º LGPD", "UE": "Art. 13 GDPR; AI Act", "EUA": "FOIA"}),
            ConstitutionalArticle("Art. 37º", "Auditoria Contínua e Independente", ArticleCategory.TRANSPARENCY,
                "Sistemas de AGI de alto risco devem passar por auditoria independente a cada 12 meses. Relatórios são públicos.",
                ["P6", "P1", "P5"], {"Brasil": "Art. 70-75 CF/88", "UE": "AI Act", "EUA": "GAO audits"}),
            ConstitutionalArticle("Art. 38º", "Registro Público de Incidentes de AGI", ArticleCategory.TRANSPARENCY,
                "Todo incidente de segurança, viés ou mau funcionamento deve ser registrado em base pública global dentro de 72 horas.",
                ["P6", "P8", "P4"], {"Brasil": "Art. 46 LGPD", "UE": "Art. 33 GDPR; AI Act", "EUA": "CISA"}),
            ConstitutionalArticle("Art. 39º", "Direito à Informação sobre Uso de AGI", ArticleCategory.TRANSPARENCY,
                "Todo ser humano tem direito de saber quando está interagindo com sistema de AGI. O disfarce de AGI como humano é crime.",
                ["P6", "P8", "P3"], {"Brasil": "Art. 6º, III LGPD", "UE": "Art. 13 GDPR; AI Act", "Califórnia": "SB 1001"}),
            ConstitutionalArticle("Art. 40º", "Cadeia de Custódia de Dados", ArticleCategory.TRANSPARENCY,
                "Os dados usados no treinamento e operação de AGI devem ter cadeia de custódia documentada. Dados de origem ilícita são inutilizáveis.",
                ["P6", "P5", "P9"], {"Brasil": "Art. 7º LGPD", "UE": "Art. 5 GDPR", "EUA": "4th Amendment"}),
            ConstitutionalArticle("Art. 41º", "Acesso Universal às Decisões do ASI-TPI", ArticleCategory.TRANSPARENCY,
                "Todas as decisões do ASI-TPI são públicas e acessíveis em todas as línguas oficiais da ONU. O sigilo processual é excepcional.",
                ["P6", "P4", "P2"], {"Brasil": "Art. 93, IX CF/88", "ONU": "Art. 10 DUDH", "EUA": "Public Trial Clause"}),
            ConstitutionalArticle("Art. 42º", "Verificação Formal como Requisito Constitucional", ArticleCategory.TRANSPARENCY,
                "Todo sistema de AGI deve ter especificação formal verificável antes da implantação, incluindo prova de segurança, análise de viés e teste de robustez.",
                ["P1", "P6", "P5"], {"Brasil": "Art. 37, caput CF/88", "UE": "AI Act", "Aviação": "DO-178C"}),

            # TÍTULO V — MEIO AMBIENTE E SUSTENTABILIDADE (Arts. 43-45)
            ConstitutionalArticle("Art. 43º", "Computação Sustentável", ArticleCategory.ENVIRONMENT,
                "O desenvolvimento e operação de sistemas de AGI devem respeitar limites de consumo energético e hídrico. Data centers devem operar com 100% energia renovável até 2035.",
                ["P7", "P4", "P6"], {"Brasil": "Art. 225 CF/88", "UE": "European Green Deal", "ONU": "ODS 7 e 13"}),
            ConstitutionalArticle("Art. 44º", "Proteção da Biodiversidade contra AGI", ArticleCategory.ENVIRONMENT,
                "Sistemas de AGI não podem causar dano direto ou indireto à biodiversidade. A modelagem climática por AGI é de interesse global e deve ser transparente.",
                ["P7", "P3", "P6"], {"Brasil": "Art. 225 CF/88", "ONU": "Convenção sobre Diversidade Biológica", "Paris": "Acordo de Paris"}),
            ConstitutionalArticle("Art. 45º", "Eficiência Energética como Direito Fundamental", ArticleCategory.ENVIRONMENT,
                "O desperdício computacional é inconstitucional. Sistemas de AGI devem ser otimizados para minimizar consumo energético por unidade de utilidade social.",
                ["P7", "P1", "P4"], {"Brasil": "Art. 170, VI CF/88", "UE": "Diretiva 2012/27/EU", "ONU": "ODS 12"}),

            # TÍTULO VI — EXECUÇÃO E FEDERAÇÃO (Arts. 46-48)
            ConstitutionalArticle("Art. 46º", "Rede Federada de Execução", ArticleCategory.ENFORCEMENT,
                "As sentenças do ASI-TPI são executadas por rede federada de nós soberanos. A execução cross-platform é garantida por Token Arkhe Bus.",
                ["P4", "P2", "P1"], {"Brasil": "Art. 144 CF/88", "Interpol": "Estatuto", "UE": "Eurojust"}),
            ConstitutionalArticle("Art. 47º", "Nós de Execução Soberanos", ArticleCategory.ENFORCEMENT,
                "Os nós de execução são operados por Estados-membros ou entidades certificadas sob supervisão nacional. A execução em território estrangeiro requer homologação local.",
                ["P4", "P3", "P2"], {"Brasil": "Art. 102, I, 'h' CF/88", "ONU": "Art. 105 Carta ONU", "UE": "Regulamento Bruxelas I"}),
            ConstitutionalArticle("Art. 48º", "Cooperação Judiciária Internacional", ArticleCategory.ENFORCEMENT,
                "Os Estados-membros comprometem-se a cooperar na execução de sentenças do ASI-TPI, inclusive mediante extradição, confiscos e suspensão de operações.",
                ["P4", "P2", "P5"], {"Brasil": "Art. 4º, IX CF/88", "ONU": "Convenção de Palermo", "UE": "Eurojust"}),

            # TÍTULO VII — EMENDAS E REVISÃO (Arts. 49-50)
            ConstitutionalArticle("Art. 49º", "Processo de Emenda Constitucional", ArticleCategory.AMENDMENT,
                "Esta Constituição pode ser emendada por proposta de 2/3 dos Estados-membros, Assembleia Global Arkhe ou Oráculo Fotônico com Φ_C > 0.95. A emenda requer ratificação por 3/4 dos Estados-membros.",
                ["P2", "P4", "P5"], {"Brasil": "Art. 60 CF/88", "EUA": "Art. V", "Alemanha": "Art. 79 GG", "UE": "Art. 48 TUE"}),
            ConstitutionalArticle("Art. 50º", "Cláusula Pétrea da Dignidade Humana", ArticleCategory.AMENDMENT,
                "Os Arts. 1º a 5º desta Constituição são cláusulas pétreas e não podem ser emendados. A dignidade humana, o direito à existência, a autonomia, a intimidade e a informação verdadeira são invioláveis e eternos.",
                ["P10", "P3", "P5"], {"Brasil": "Art. 60, §4º, IV CF/88", "Alemanha": "Art. 79(3) GG", "EUA": "Implicit in constitutional structure"}),
        ]

        for article in self.ARTICLES:
            article.seal = hashlib.sha3_256(
                f"{article.number}:{article.title}:{article.category.value}:{json.dumps(article.principles)}".encode()
            ).hexdigest()

    def _generate_constitution_seal(self) -> str:
        payload = json.dumps({
            "document": "Constituição Global Arkhe",
            "articles": len(self.ARTICLES),
            "principles": "P1-P10",
            "preamble_hash": hashlib.sha3_256(self.PREAMBLE.encode()).hexdigest()[:16],
            "timestamp": time.time()
        }, sort_keys=True)
        return hashlib.sha3_256(payload.encode()).hexdigest()

    def get_article(self, number: str) -> Optional[ConstitutionalArticle]:
        for article in self.ARTICLES:
            if article.number == number:
                return article
        return None

    def get_articles_by_principle(self, principle: str) -> List[ConstitutionalArticle]:
        return [a for a in self.ARTICLES if principle in a.principles]

    def get_articles_by_category(self, category: ArticleCategory) -> List[ConstitutionalArticle]:
        return [a for a in self.ARTICLES if a.category == category]

    def validate_against_national_constitution(self, country: str, article_numbers: List[str]) -> Dict:
        results = {}
        for num in article_numbers:
            article = self.get_article(num)
            if article:
                parallel = article.national_parallels.get(country, "Não mapeado")
                results[num] = {
                    "title": article.title,
                    "national_parallel": parallel,
                    "has_parallel": parallel != "Não mapeado",
                    "principles": article.principles
                }
            else:
                results[num] = {
                    "title": "Artigo não encontrado",
                    "national_parallel": "Não mapeado",
                    "has_parallel": False,
                    "principles": []
                }
        all_have_parallel = bool(results) and all(r["has_parallel"] for r in results.values())
        return {
            "country": country,
            "articles_validated": results,
            "all_have_national_basis": all_have_parallel,
            "validation_seal": hashlib.sha3_256(f"{country}:{article_numbers}:{time.time()}".encode()).hexdigest()
        }

    def get_full_constitution(self) -> Dict:
        return {
            "preamble": self.PREAMBLE.strip(),
            "articles": [
                {
                    "number": a.number,
                    "title": a.title,
                    "category": a.category.value,
                    "text": a.text,
                    "principles": a.principles,
                    "national_parallels": a.national_parallels,
                    "seal": a.seal
                }
                for a in self.ARTICLES
            ],
            "total_articles": len(self.ARTICLES),
            "constitution_seal": self.constitution_seal,
            "categories": list(set(a.category.value for a in self.ARTICLES)),
            "principles_coverage": {
                p: len(self.get_articles_by_principle(p))
                for p in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
            }
        }


def activate_global_constitution():
    print("="*70)
    print("📜 CONSTITUIÇÃO GLOBAL PARA A ERA DA SUPERINTELIGÊNCIA")
    print("   ARKHE Ω-TEMP v∞.Ω — SUBSTRATO 262")
    print("="*70)

    constitution = ArkheGlobalConstitution()

    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   Total de artigos: {len(constitution.ARTICLES)}")
    print(f"   Categorias: {len(set(a.category.value for a in constitution.ARTICLES))}")
    print(f"   Selo: {constitution.constitution_seal}")

    print(f"\n📋 COBERTURA DOS PRINCÍPIOS:")
    for p in ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]:
        count = len(constitution.get_articles_by_principle(p))
        bar = "█" * count + "░" * (10 - count)
        print(f"   {p}: {bar} ({count})")

    print(f"\n📑 ARTIGOS POR CATEGORIA:")
    for cat in ArticleCategory:
        articles = constitution.get_articles_by_category(cat)
        print(f"   {cat.value.upper()}: {len(articles)} artigos")

    validation = constitution.validate_against_national_constitution(
        "Brasil", ["Art. 1º", "Art. 5º", "Art. 26º", "Art. 36º", "Art. 43º", "Art. 50º"]
    )
    print(f"\n🇧🇷 VALIDAÇÃO CF/88: {'✅ TODOS MAPEADOS' if validation['all_have_national_basis'] else '❌ FALTANDO'}")

    full = constitution.get_full_constitution()
    print(f"\n🔐 SELO CANÔNICO: {full['constitution_seal']}")

    print("\n" + "="*70)
    print("📜 CONSTITUIÇÃO GLOBAL ARKHE — ATIVADA")
    print("="*70)

    return constitution, full


if __name__ == "__main__":
    constitution, full_report = activate_global_constitution()
    seal_262 = hashlib.sha3_256(
        f"substrate_262:global_constitution:{full_report['total_articles']}:{len(full_report['categories'])}:{time.time()}".encode()
    ).hexdigest()
    print(f"\n🔐 CANONICAL SEAL (Substrate 262): {seal_262}")