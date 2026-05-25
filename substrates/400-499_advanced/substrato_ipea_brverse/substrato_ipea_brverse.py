import json
import tempfile
import os

class SubstratoIpeaBrverse:
    def canonize(self):
        report = {
            "Title": "brverse - Lista de pacotes de R para acesso a dados brasileiros",
            "Description": "Esse repositório traz uma lista de pacotes de R para acesso a dados brasileiros, o que estamos chamando carinhosamente de 'brverse'. Nossa política é colocar somente pacotes que estejam publicados no CRAN.",
            "Features": [
                "Economia e Finanças: pacotes como ipeadatar, orcamentoBR, deflateBR, etc.",
                "Educação: educabR",
                "Eleitorais e Política: electionsBR, speechbr, agregR",
                "Espaciais e de endereços: enderecobr, geobr, geocodebr, cepR",
                "Meio ambiente: brclimr, BrazilMet, florabr, flora",
                "Nomes: genderBR, metaphonebr, nomesbr, SoundexBR",
                "População e dados socioeconômicos: censobr, brpop, PNADcIBGE, PNADCperiods, datazoom.social",
                "Saúde: microdatasus, PNSIBGE, COVIDIBGE",
                "Segurança pública: BrazilCrime, ispdata",
                "Transportes: flightsbr, odbr, aopdata",
                "Miscelânea: abjData, aebdata, basedosdados, datazoom.amazonia, documentosbr, numbersBR, owdbr, sidrar, ibger"
            ],
            "Architecture": [
                "Curated list of R packages categorized by domain",
                "Requires packages to be published on CRAN"
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_ipea_brverse_", text=True)
        with os.fdopen(fd, 'w', encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print("Canonized ipea/brverse. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoIpeaBrverse()
    substrate.canonize()
