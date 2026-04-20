#!/usr/bin/env python3
"""
owl_semver_diff.py
Compara duas ontologias OWL e determina o impacto SemVer da mudança.
"""

import sys
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from typing import Set, Tuple, Literal
import json

OWL_NS = Namespace("http://www.w3.org/2002/07/owl#")

class OWLSemVerDiff:
    def __init__(self, old_path: str, new_path: str):
        self.old_g = Graph()
        self.new_g = Graph()
        self.old_g.parse(old_path, format="xml")
        self.new_g.parse(new_path, format="xml")

    def _get_axioms(self, g: Graph) -> Set[Tuple]:
        """Extrai axiomas relevantes como tuplas hashable."""
        axioms = set()
        for s in g.subjects(RDF.type, OWL.Class):
            axioms.add(("ClassDeclaration", str(s)))
        for s, o in g.subject_objects(RDFS.subClassOf):
            axioms.add(("SubClassOf", str(s), str(o)))
        for s, o in g.subject_objects(OWL.disjointWith):
            axioms.add(("DisjointWith", str(s), str(o)))
        for s in g.subjects(RDF.type, OWL.ObjectProperty):
            axioms.add(("ObjectProperty", str(s)))
        return axioms

    def classify_change(self) -> Tuple[Literal["MAJOR", "MINOR", "PATCH"], dict]:
        old_axioms = self._get_axioms(self.old_g)
        new_axioms = self._get_axioms(self.new_g)

        removed = old_axioms - new_axioms
        added = new_axioms - old_axioms

        is_major = False
        breaking = []

        for ax in removed:
            if ax[0] in ("ClassDeclaration", "ObjectProperty", "SubClassOf"):
                is_major = True
                breaking.append(ax)

        if is_major:
            return "MAJOR", {"breaking": breaking}
        elif added:
            return "MINOR", {"added": list(added)}
        else:
            return "PATCH", {}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
    diff = OWLSemVerDiff(sys.argv[1], sys.argv[2])
    semver, report = diff.classify_change()
    print(json.dumps({"semver": semver, "report": report}, indent=2))
