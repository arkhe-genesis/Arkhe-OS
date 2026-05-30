# clarity_gate.py — Substrato 958
# Toda landing page da Catedral deve passar neste teste antes do deploy.

def test_5_segundos(hero_section):
    """
    Simula o cérebro de um visitante em 5 segundos.
    Retorna True se a hero section comunicar clareza imediata.
    """
    perguntas_respondidas = 0

    # 1. O que é isso?
    if hero_section.headline and not é_abstrata(hero_section.headline):
        if comunica_funcao_em_linguagem_do_cliente(hero_section.headline):
            perguntas_respondidas += 1

    # 2. Isso é pra mim?
    if hero_section.subheadline:
        if crava_icp(hero_section.subheadline) and crava_resultado(hero_section.subheadline):
            perguntas_respondidas += 1

    # 3. Por que eu deveria me importar agora?
    if hero_section.prova_social and hero_section.cta:
        if hero_section.prova_social.contem_logos_ou_numeros and hero_section.cta.especifico:
            perguntas_respondidas += 1

    return perguntas_respondidas >= 3

def é_abstrata(headline):
    termos_proibidos = ["revolucione", "plataforma definitiva", "solução integrada",
                        "ecossistema", "sinergia", "next-gen", "powered by AI"]
    return any(termo in headline.lower() for termo in termos_proibidos)

# Mocked functions and classes for standalone validation
class HeroSection:
    def __init__(self, headline=None, subheadline=None, prova_social=None, cta=None):
        self.headline = headline
        self.subheadline = subheadline
        self.prova_social = prova_social
        self.cta = cta

class ProvaSocial:
    def __init__(self, contem_logos_ou_numeros=False):
        self.contem_logos_ou_numeros = contem_logos_ou_numeros

class CTA:
    def __init__(self, especifico=False):
        self.especifico = especifico

def comunica_funcao_em_linguagem_do_cliente(headline):
    # Dummy implementation for tests
    return True

def crava_icp(subheadline):
    # Dummy implementation for tests
    return True

def crava_resultado(subheadline):
    # Dummy implementation for tests
    return True

if __name__ == "__main__":
    # Test with good data
    ps = ProvaSocial(contem_logos_ou_numeros=True)
    cta = CTA(especifico=True)
    hero = HeroSection(
        headline="Gerencie suas finanças de forma simples",
        subheadline="Para pequenas empresas aumentarem seus lucros",
        prova_social=ps,
        cta=cta
    )
    print("Passou:", test_5_segundos(hero))

    # Test with abstract headline
    hero.headline = "Solução integrada next-gen para sinergia"
    print("Passou (deve falhar):", test_5_segundos(hero))
