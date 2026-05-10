#!/usr/bin/env python3
"""Demonstração do parser de arkhe-lang para intenção molecular."""
from cathedral_chemputation.intent.parser import ArkheMolecularParser

def main():
    arkhe_code = """
    molecule {
      target: "covalent_inhibitor",
      protein_target: "KRAS_G12D",
      constraints: {
        IC50_max: "10nM",
        synthetic_steps_max: 5
      }
    }
    """
    intent = ArkheMolecularParser.parse(arkhe_code, intent_id="kras_g12d_v1")
    print(f"✅ Intent parsed: {intent.intent_id}")

if __name__ == "__main__":
    main()
