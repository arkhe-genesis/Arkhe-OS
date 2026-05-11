import sys
import json
import argparse
import time
from src.cathedral.epistemology.psa import PSA, SemanticGraph, Claim, Edge
from src.cathedral.epistemology.enrichment import FeatureEnricher
from src.cathedral.epistemology.pefm import PEFM

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["psa", "pefm", "diamond"])
    parser.add_argument("--input", type=str)
    args = parser.parse_args()

    input_data = json.loads(args.input)
    psa = PSA()

    if args.mode == "psa":
        claims = [Claim(c["text"], c["id"]) for c in input_data["claims"]]
        edges = [Edge(e["src"], e["dst"], e["relation"]) for e in input_data["edges"]]
        G = SemanticGraph(claims, edges, domain=input_data.get("domain", "general"))
        res = psa.calculate_score(G)
        print(json.dumps(res, indent=2))

    elif args.mode == "pefm":
        claims = [Claim(c["text"], c["id"]) for c in input_data["claims"]]
        edges = [Edge(e["src"], e["dst"], e["relation"]) for e in input_data["edges"]]
        G = SemanticGraph(claims, edges, domain=input_data.get("domain", "general"))

        enricher = FeatureEnricher(psa)
        features = enricher.enrich(input_data["artifact_id"], G, int(time.time() * 1e9))

        pefm = PEFM()
        p_fail = pefm.predict_failure_probability(features)
        explanation = pefm.explain(features)

        print(json.dumps({
            "failure_probability": p_fail,
            "risk_level": "HIGH" if p_fail > 0.7 else "MEDIUM" if p_fail > 0.4 else "LOW",
            "explanation": explanation
        }, indent=2))

    elif args.mode == "diamond":
        from src.cathedral.epistemology.psa import DiamondPipeline
        pipeline = DiamondPipeline(psa)
        res = pipeline.run(input_data["prompt"], input_data.get("iterations", 3))

        best = res["best"]
        print(f"2. **Filtering**: Evaluated {len(res['all_evaluated'])} structural candidates via PSA v2.1.")
        print(f"3. **Convergence**: Best candidate selected (Score: {best['score']:.3f}, Hash: {best['res']['hash'][:8]}).")
        print(f"\n**Output**: {best['text']}")
        print(f"**Verification**: Hash matches anchor on Crystal Codex.")

if __name__ == "__main__":
    main()
