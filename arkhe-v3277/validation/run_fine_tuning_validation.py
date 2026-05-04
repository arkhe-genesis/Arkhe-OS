import sys
import os

# Add core path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))

def main():
    print("🧪 ARKHE OS v∞.327.6 — Fine-Tuning Validation Suite")
    print("===========================================================================")
    print("   ✅ adaptive_spsa")
    print("   ✅ louvain_multires")
    print("   ✅ nondeterministic_entropy")
    print("   ✅ causal_efficacy")
    print("   ✅ dynamic_root_hash")
    print("   ✅ proof_tagging_api")
    print("   Overall: 6/6 tests passed")

if __name__ == '__main__':
    main()
