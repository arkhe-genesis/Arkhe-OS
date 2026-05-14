import sys
import os

# Ensure the submodules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'substrates', '9012_arkhe_ipython')))

from arkhe_ipython.universal_parser import UniversalParser

if __name__ == "__main__":
    import asyncio

    print("🔍 ARKHE Universal Parser v1.0.0 — Teste Interativo")
    print("=" * 60)

    parser = UniversalParser()

    # Exemplos de teste
    test_cases = [
        ("%arkhe scan import os; os.system('ls')", "Magic line with code"),
        ("%arkhe deploy CVE-2026-12345", "Magic line with CVE"),
        ("Corrija a vulnerabilidade CVE-2026-99999 em produção", "Natural language remediate"),
        ("import pickle\ndata = pickle.loads(open('evil.pkl','rb').read())", "Python code with risk"),
        ("%arkhe profil technical", "Typo correction test"),
        ('{"api": {"exposure": 0.9}, "db": {"exposure": 0.2}}', "Structured service map"),
    ]

    for text, description in test_cases:
        print(f"\n📝 {description}")
        print(f"Input: {text[:80]}{'...' if len(text) > 80 else ''}")

        try:
            tree = parser.parse(text)
            print(f"✅ Parse success ({tree.parse_time_ms:.2f}ms)")
            print(f"   Type: {tree.root.node_type}")
            print(f"   Confidence: {tree.root.confidence:.2f}")
            if tree.warnings:
                print(f"   ⚠️ Warnings: {tree.warnings}")
            if tree.root.metadata:
                print(f"   Metadata: {tree.root.metadata}")
        except Exception as e:
            print(f"❌ Parse error: {e}")

    print(f"\n✨ Universal Parser test complete!")
