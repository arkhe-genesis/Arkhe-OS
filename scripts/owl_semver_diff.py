#!/usr/bin/env python3
"""
owl_semver_diff.py v3.0
Compara ontologias OWL e determina impacto SemVer + Segurança + Arquitetura.
"""
import sys
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from typing import Set, Tuple, Literal
import json

OWL_NS = Namespace("http://www.w3.org/2002/07/owl#")
ARKHE = Namespace("http://arkhe.ai/ontology/2026#")

SECURITY_ENTITIES = {
    str(ARKHE.SussurroDeSubversao),
    str(ARKHE.RachaduraNaMuralha),
    str(ARKHE.RunaProibida),
    str(ARKHE.GuardiaoDoPortao),
    str(ARKHE.BibliotecaArcana),
    str(ARKHE.exploraRachadura),
    str(ARKHE.contemRunaProibida),
    str(ARKHE.usaBibliotecaArcana),
    str(ARKHE.usaChaveMestra),
}

# Entidades arquiteturais que, se modificadas, alteram a fundação computacional
ARCHITECTURAL_ENTITIES = {
    str(ARKHE.Transformer),
    str(ARKHE.AttentionHead),
    str(ARKHE.FeedForwardNetwork),
    str(ARKHE.LayerNormalization),
    str(ARKHE.ResidualConnection),
    str(ARKHE.PositionalEncoding),
    str(ARKHE.approximates),
    str(ARKHE.hasCliffordEquivalent),
    str(ARKHE.requiresJustification),
}

class OWLSemVerDiff:
    def __init__(self, old_path: str, new_path: str):
        self.old_g = Graph()
        self.new_g = Graph()

        def parse_graph(g, path):
            try:
                g.parse(path, format="turtle")
            except:
                try:
                    g.parse(path, format="xml")
                except Exception as e:
                    print(f"Error parsing {path}: {e}")

        parse_graph(self.old_g, old_path)
        parse_graph(self.new_g, new_path)

    def _get_axioms(self, g: Graph) -> Set[Tuple]:
        axioms = set()
        for s in g.subjects(RDF.type, OWL.Class):
            axioms.add(("ClassDeclaration", str(s)))
        for s, o in g.subject_objects(RDFS.subClassOf):
            axioms.add(("SubClassOf", str(s), str(o)))
        for s, o in g.subject_objects(OWL.disjointWith):
            axioms.add(("DisjointWith", str(s), str(o)))
        for s in g.subjects(RDF.type, OWL.ObjectProperty):
            axioms.add(("ObjectProperty", str(s)))
        for s, o in g.subject_objects(RDFS.domain):
            axioms.add(("Domain", str(s), str(o)))
        for s, o in g.subject_objects(RDFS.range):
            axioms.add(("Range", str(s), str(o)))
        for s, o in g.subject_objects(OWL.inverseOf):
            axioms.add(("InverseOf", str(s), str(o)))

        # Captura instâncias de arquitetura
        for s in g.subjects(RDF.type, ARKHE.Transformer):
            axioms.add(("Instance", "Transformer", str(s)))
        for s in g.subjects(RDF.type, ARKHE.AttentionHead):
            axioms.add(("Instance", "AttentionHead", str(s)))
        for s in g.subjects(RDF.type, ARKHE.FeedForwardNetwork):
            axioms.add(("Instance", "FFN", str(s)))
        return axioms

    def _is_security_axiom(self, ax: Tuple) -> bool:
        return any(ent in str(ax) for ent in SECURITY_ENTITIES)

    def _is_architectural_axiom(self, ax: Tuple) -> bool:
        return any(ent in str(ax) for ent in ARCHITECTURAL_ENTITIES)

    def classify_change(self) -> Tuple[Literal["ARCHITECTURAL_MAJOR", "SECURITY_MAJOR", "MAJOR", "MINOR", "PATCH"], dict]:
        old_axioms = self._get_axioms(self.old_g)
        new_axioms = self._get_axioms(self.new_g)

        removed = old_axioms - new_axioms
        added = new_axioms - old_axioms

        report = {
            "removed_axioms": [list(r) for r in removed],
            "added_axioms": [list(a) for a in added],
            "breaking_changes": [],
            "security_changes": [],
            "architectural_changes": [],
            "safe_changes": []
        }

        is_arch_major = False
        is_security_major = False
        is_major = False

        for ax in removed:
            if self._is_architectural_axiom(ax):
                is_arch_major = True
                report["architectural_changes"].append({
                    "type": "ARCHITECTURE_SURFACE_REDUCED",
                    "axiom": ax,
                    "reason": "Remoção de entidade arquitetural altera a fundação computacional"
                })
            elif self._is_security_axiom(ax):
                is_security_major = True
                report["security_changes"].append({
                    "type": "SECURITY_SURFACE_REDUCED",
                    "axiom": ax,
                    "reason": "Remoção de entidade de segurança altera a superfície de ameaça"
                })
            elif ax[0] in ("ClassDeclaration", "ObjectProperty"):
                is_major = True
                report["breaking_changes"].append({
                    "type": "ENTITY_REMOVAL",
                    "axiom": ax,
                    "reason": "Remoção de classe ou propriedade quebra queries existentes"
                })
            elif ax[0] == "SubClassOf":
                is_major = True
                report["breaking_changes"].append({
                    "type": "HIERARCHY_CHANGE",
                    "axiom": ax,
                    "reason": "Alteração na hierarquia de classes afeta inferência"
                })

        for ax in added:
            if self._is_architectural_axiom(ax):
                is_arch_major = True
                report["architectural_changes"].append({
                    "type": "ARCHITECTURE_SURFACE_EXPANDED",
                    "axiom": ax,
                    "reason": "Adição de entidade arquitetural requer validação Cliffordiana"
                })
            elif self._is_security_axiom(ax):
                is_security_major = True
                report["security_changes"].append({
                    "type": "SECURITY_SURFACE_EXPANDED",
                    "axiom": ax,
                    "reason": "Adição de entidade de segurança requer reavaliação do modelo de ameaça"
                })
            elif ax[0] == "DisjointWith":
                is_major = True
                report["breaking_changes"].append({
                    "type": "DISJOINTNESS_ADDED",
                    "axiom": ax,
                    "reason": "Nova disjunção entre classes existentes pode invalidar instâncias"
                })
            elif ax[0] == "Instance" and ax[1] in ("Transformer", "AttentionHead", "FFN"):
                is_arch_major = True
                report["architectural_changes"].append({
                    "type": "DEGENERATE_ARCHITECTURE_ADDED",
                    "axiom": ax,
                    "reason": "Nova instância de Transformer/Atencao/FFN detectada. Requer justificativa Cliffordiana."
                })

        if is_arch_major:
            return "ARCHITECTURAL_MAJOR", report
        if is_security_major:
            return "SECURITY_MAJOR", report
        if is_major:
            return "MAJOR", report
        elif added:
            return "MINOR", report
        else:
            return "PATCH", report

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python owl_semver_diff.py old.owl new.owl")
        sys.exit(1)

    diff = OWLSemVerDiff(sys.argv[1], sys.argv[2])
    semver, report = diff.classify_change()
    report["semver"] = semver

    print(json.dumps(report, indent=2))

    if semver == "ARCHITECTURAL_MAJOR":
        sys.exit(4)  # Código 4: Arquitetura degenerada não justificada
    elif semver == "SECURITY_MAJOR":
        sys.exit(3)
    elif semver == "MAJOR":
        sys.exit(2)
    elif semver == "MINOR":
        sys.exit(1)
    else:
        sys.exit(0)
