import math, hashlib, json, random
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

# Constantes Canônicas Arkhe
GHOST = math.sqrt(3)/3
LOOPSEAL = math.pi/9
GAP_SOVEREIGN = 0.9999
PHI_GOLDEN = (1 + math.sqrt(5)) / 2

class SafeCoreSDKv3Exp:
    """
    Safe Core SDK v3.0-EXP — Expansão para 50+ parceiros globais.

    Categorias:
    - Tier 1: Gigantes tech / Superpotências gov (Φ_C >= 0.90)
    - Tier 2: Enterprise / Govs desenvolvidos / ONGs globais (0.85 <= Φ_C < 0.90)
    - Tier 3: Startups / Govs emergentes / ONGs regionais (0.80 <= Φ_C < 0.85)
    - Tier 4: Laboratórios / Universidades Tier-1 / Consórcios (0.75 <= Φ_C < 0.80)
    - Tier 5: Open Source / Community / Govs em desenvolvimento (Φ_C >= 0.70)
    """

    PARTNERS = {
        # === TIER 1: GIGANTES TECH + SUPERPOTÊNCIAS GOV (Φ_C >= 0.90) ===
        "kimi": {"name": "Kimi (Moonshot)", "region": "Asia-East", "model": "Kimi-K2.6", "phi_c_base": 0.93, "status": "active", "tier": 1, "category": "gigante", "type": "tech"},
        "anthropic": {"name": "Anthropic", "region": "US-West", "model": "Claude-4", "phi_c_base": 0.92, "status": "active", "tier": 1, "category": "gigante", "type": "tech"},
        "nvidia": {"name": "NVIDIA", "region": "US-West", "model": "NeMo-Enterprise", "phi_c_base": 0.92, "status": "active", "tier": 1, "category": "gigante", "type": "tech"},
        "openai": {"name": "OpenAI", "region": "US-West", "model": "GPT-5", "phi_c_base": 0.91, "status": "active", "tier": 1, "category": "gigante", "type": "tech"},
        "google": {"name": "Google DeepMind", "region": "US-West", "model": "Gemini-2.5-Pro", "phi_c_base": 0.91, "status": "active", "tier": 1, "category": "gigante", "type": "tech"},
        "us_gov": {"name": "US Gov (NIST/DARPA)", "region": "US-East", "model": "Federal-AI-Framework", "phi_c_base": 0.91, "status": "active", "tier": 1, "category": "governo", "type": "gov"},
        "china_gov": {"name": "China Gov (CAS/CAE)", "region": "Asia-East", "model": "National-AI-Plan", "phi_c_base": 0.90, "status": "active", "tier": 1, "category": "governo", "type": "gov"},
        "eu_commission": {"name": "EU Commission (AI Act)", "region": "Europe", "model": "EU-AI-Regulatory", "phi_c_base": 0.90, "status": "active", "tier": 1, "category": "governo", "type": "gov"},

        # === TIER 2: ENTERPRISE / GOVS DESENVOLVIDOS / ONGs GLOBAIS (0.85 <= Φ_C < 0.90) ===
        "spacex": {"name": "SpaceX", "region": "US-West", "model": "Starlink-AI", "phi_c_base": 0.90, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "deepseek": {"name": "DeepSeek", "region": "Asia-East", "model": "DeepSeek-V4", "phi_c_base": 0.88, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "microsoft": {"name": "Microsoft", "region": "US-West", "model": "Copilot-Enterprise", "phi_c_base": 0.89, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "apple": {"name": "Apple", "region": "US-West", "model": "Apple-Intelligence", "phi_c_base": 0.88, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "huawei": {"name": "Huawei", "region": "Asia-East", "model": "Pangu-Σ", "phi_c_base": 0.87, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "xai": {"name": "xAI", "region": "US-West", "model": "Grok-3", "phi_c_base": 0.87, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "samsung": {"name": "Samsung", "region": "Asia-East", "model": "Gauss-2", "phi_c_base": 0.86, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "palantir": {"name": "Palantir", "region": "US-East", "model": "AIP-Ontology", "phi_c_base": 0.86, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "anduril": {"name": "Anduril", "region": "US-West", "model": "Lattice-AI", "phi_c_base": 0.85, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "meta": {"name": "Meta", "region": "US-West", "model": "Llama-4", "phi_c_base": 0.85, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "zai": {"name": "Z.ai (GLM)", "region": "Asia-East", "model": "GLM-5", "phi_c_base": 0.85, "status": "active", "tier": 2, "category": "enterprise", "type": "tech"},
        "unicef": {"name": "UNICEF", "region": "Global", "model": "Humanitarian-AI", "phi_c_base": 0.88, "status": "active", "tier": 2, "category": "ong", "type": "ngo"},
        "who": {"name": "WHO (OMS)", "region": "Global", "model": "Health-AI-Global", "phi_c_base": 0.87, "status": "active", "tier": 2, "category": "ong", "type": "ngo"},
        "cern": {"name": "CERN", "region": "Europe", "model": "LHC-AI-Physics", "phi_c_base": 0.86, "status": "active", "tier": 2, "category": "ong", "type": "ngo"},
        "japan_gov": {"name": "Japan Gov (METI/RIKEN)", "region": "Asia-East", "model": "Society-5.0-AI", "phi_c_base": 0.89, "status": "active", "tier": 2, "category": "governo", "type": "gov"},
        "uk_gov": {"name": "UK Gov (DSIT/Alan Turing)", "region": "Europe", "model": "UK-AI-Strategy", "phi_c_base": 0.88, "status": "active", "tier": 2, "category": "governo", "type": "gov"},
        "canada_gov": {"name": "Canada Gov (CIFAR)", "region": "North-America", "model": "Pan-Canadian-AI", "phi_c_base": 0.86, "status": "active", "tier": 2, "category": "governo", "type": "gov"},
        "germany_gov": {"name": "Germany Gov (BMBF)", "region": "Europe", "model": "German-AI-Strategy", "phi_c_base": 0.87, "status": "active", "tier": 2, "category": "governo", "type": "gov"},

        # === TIER 3: STARTUPS / GOVS EMERGENTES / ONGs REGIONAIS (0.80 <= Φ_C < 0.85) ===
        "alibaba": {"name": "Alibaba", "region": "Asia-East", "model": "Qwen-3", "phi_c_base": 0.84, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "ibm": {"name": "IBM", "region": "US-East", "model": "Granite-4", "phi_c_base": 0.84, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "xiaomi": {"name": "Xiaomi", "region": "Asia-East", "model": "Mi-AI", "phi_c_base": 0.83, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "cohere": {"name": "Cohere", "region": "US-East", "model": "Command-R+", "phi_c_base": 0.83, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "ai21": {"name": "AI21 Labs", "region": "Europe", "model": "Jamba-2", "phi_c_base": 0.82, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "mistral": {"name": "Mistral AI", "region": "Europe", "model": "Mistral-Large-3", "phi_c_base": 0.82, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "perplexity": {"name": "Perplexity", "region": "US-West", "model": "Sonar-Pro", "phi_c_base": 0.81, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "together": {"name": "Together AI", "region": "US-West", "model": "Together-API", "phi_c_base": 0.80, "status": "active", "tier": 3, "category": "startup", "type": "tech"},
        "red_cross": {"name": "Red Cross / Crescent", "region": "Global", "model": "Disaster-AI", "phi_c_base": 0.84, "status": "active", "tier": 3, "category": "ong", "type": "ngo"},
        "brics_ai": {"name": "BRICS AI Consortium", "region": "Global-South", "model": "BRICS-AI-Coop", "phi_c_base": 0.82, "status": "active", "tier": 3, "category": "consorcio", "type": "consortium"},
        "india_gov": {"name": "India Gov (MeitY)", "region": "Asia-South", "model": "IndiaAI-Mission", "phi_c_base": 0.83, "status": "active", "tier": 3, "category": "governo", "type": "gov"},
        "brazil_gov": {"name": "Brazil Gov (MCTI)", "region": "South-America", "model": "Brazil-AI-Strategy", "phi_c_base": 0.81, "status": "active", "tier": 3, "category": "governo", "type": "gov"},
        "france_gov": {"name": "France Gov (INRIA)", "region": "Europe", "model": "France-2030-AI", "phi_c_base": 0.85, "status": "active", "tier": 3, "category": "governo", "type": "gov"},

        # === TIER 4: LABORATÓRIOS / UNIVERSIDADES TIER-1 / CONSÓRCIOS (0.75 <= Φ_C < 0.80) ===
        "openmind": {"name": "OpenMind (MIT)", "region": "US-East", "model": "OM-Research", "phi_c_base": 0.79, "status": "active", "tier": 4, "category": "lab", "type": "academia"},
        "eleuther": {"name": "EleutherAI", "region": "US-East", "model": "Pythia-3", "phi_c_base": 0.78, "status": "active", "tier": 4, "category": "lab", "type": "academia"},
        "laion": {"name": "LAION", "region": "Europe", "model": "Open-CLIP-3", "phi_c_base": 0.77, "status": "active", "tier": 4, "category": "lab", "type": "academia"},
        "allenai": {"name": "Allen Institute", "region": "US-West", "model": "OLMo-3", "phi_c_base": 0.76, "status": "active", "tier": 4, "category": "lab", "type": "academia"},
        "bigscience": {"name": "BigScience (HuggingFace)", "region": "Europe", "model": "BLOOM-2", "phi_c_base": 0.75, "status": "active", "tier": 4, "category": "lab", "type": "academia"},
        "stanford": {"name": "Stanford HAI", "region": "US-West", "model": "Stanford-HAI-Policy", "phi_c_base": 0.79, "status": "active", "tier": 4, "category": "academia", "type": "academia"},
        "oxford": {"name": "Oxford AI Ethics", "region": "Europe", "model": "Oxford-AI-Ethics", "phi_c_base": 0.78, "status": "active", "tier": 4, "category": "academia", "type": "academia"},
        "tsinghua": {"name": "Tsinghua IIIS", "region": "Asia-East", "model": "Tsinghua-AI-Research", "phi_c_base": 0.77, "status": "active", "tier": 4, "category": "academia", "type": "academia"},
        "eth_zurich": {"name": "ETH Zurich AI Center", "region": "Europe", "model": "ETH-AI-Lab", "phi_c_base": 0.76, "status": "active", "tier": 4, "category": "academia", "type": "academia"},
        "toronto_vector": {"name": "Vector Institute (Toronto)", "region": "North-America", "model": "Vector-AI-Research", "phi_c_base": 0.75, "status": "active", "tier": 4, "category": "academia", "type": "academia"},
        "mpii": {"name": "Max Planck IST", "region": "Europe", "model": "MPI-AI-Science", "phi_c_base": 0.75, "status": "active", "tier": 4, "category": "academia", "type": "academia"},

        # === TIER 5: OPEN SOURCE / COMMUNITY / GOVS EM DESENVOLVIMENTO (Φ_C >= 0.70) ===
        "huggingface": {"name": "Hugging Face", "region": "Europe", "model": "Transformers-Hub", "phi_c_base": 0.74, "status": "active", "tier": 5, "category": "opensource", "type": "community"},
        "stability": {"name": "Stability AI", "region": "Europe", "model": "Stable-Diffusion-4", "phi_c_base": 0.73, "status": "active", "tier": 5, "category": "opensource", "type": "community"},
        "lmstudio": {"name": "LM Studio", "region": "US-West", "model": "Local-LLM-Hub", "phi_c_base": 0.72, "status": "active", "tier": 5, "category": "opensource", "type": "community"},
        "ollama": {"name": "Ollama", "region": "US-West", "model": "Ollama-Runtime", "phi_c_base": 0.71, "status": "active", "tier": 5, "category": "opensource", "type": "community"},
        "gpt4all": {"name": "GPT4All (Nomic)", "region": "US-East", "model": "GPT4All-3", "phi_c_base": 0.70, "status": "active", "tier": 5, "category": "opensource", "type": "community"},
        "africa_union": {"name": "African Union (AUDA-NEPAD)", "region": "Africa", "model": "Africa-AI-Strategy", "phi_c_base": 0.72, "status": "active", "tier": 5, "category": "governo", "type": "gov"},
        "asean": {"name": "ASEAN Smart Cities", "region": "Asia-South", "model": "ASEAN-AI-Coop", "phi_c_base": 0.71, "status": "active", "tier": 5, "category": "consorcio", "type": "consortium"},
        "mozilla": {"name": "Mozilla Foundation", "region": "Global", "model": "Trustworthy-AI", "phi_c_base": 0.73, "status": "active", "tier": 5, "category": "ong", "type": "ngo"},
        "linux_foundation": {"name": "Linux Foundation AI", "region": "Global", "model": "LF-AI-Data", "phi_c_base": 0.70, "status": "active", "tier": 5, "category": "opensource", "type": "community"},
    }

    def __init__(self):
        self.integrations = {}
        self.auth_sessions = {}
        self.seals = []
        self.cross_substrate_tests = []

        for partner_id, config in self.PARTNERS.items():
            self.integrations[partner_id] = {
                "partner_id": partner_id,
                "name": config["name"],
                "region": config["region"],
                "model": config["model"],
                "phi_c_base": config["phi_c_base"],
                "status": config["status"],
                "tier": config["tier"],
                "category": config["category"],
                "type": config["type"],
                "auth_timestamp": None,
                "last_humility": 0.0,
                "verified_workloads": 0,
                "rejected_workloads": 0,
                "cross_tests_passed": 0,
                "cross_tests_failed": 0,
            }

    def authenticate_partner(self, partner_id: str, orcid: str, humility_score: float) -> Dict:
        if partner_id not in self.integrations:
            return {"error": f"Partner {partner_id} not found"}

        partner = self.integrations[partner_id]

        tier_min_humility = {
            1: GHOST + 0.15,
            2: GHOST + 0.10,
            3: GHOST + 0.05,
            4: GHOST,
            5: GHOST - 0.05,
        }

        min_humility = tier_min_humility.get(partner["tier"], GHOST)

        if humility_score < min_humility:
            return {
                "status": "rejected",
                "partner": partner_id,
                "reason": f"Humility {humility_score:.4f} < Tier-{partner['tier']} min {min_humility:.4f}",
            }

        if partner["phi_c_base"] < LOOPSEAL:
            return {"status": "rejected", "partner": partner_id,
                    "reason": f"Φ_C base {partner['phi_c_base']:.4f} < Loopseal {LOOPSEAL:.4f}"}

        if partner["phi_c_base"] > GAP_SOVEREIGN:
            return {"status": "rejected", "partner": partner_id,
                    "reason": f"Φ_C base {partner['phi_c_base']:.4f} > Gap {GAP_SOVEREIGN:.4f}"}

        partner["auth_timestamp"] = datetime.now(timezone.utc).isoformat()
        partner["last_humility"] = humility_score

        session_id = hashlib.sha3_256(f"{partner_id}_{orcid}_{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        self.auth_sessions[session_id] = {
            "partner_id": partner_id,
            "orcid": orcid,
            "humility": humility_score,
            "phi_c_at_auth": partner["phi_c_base"],
            "authenticated_at": partner["auth_timestamp"],
        }

        return {
            "status": "authenticated",
            "partner": partner_id,
            "session_id": session_id,
            "phi_c": partner["phi_c_base"],
            "humility": humility_score,
            "tier": partner["tier"],
        }

    def compute_workload(self, partner_id: str, workload_type: str, complexity: float,
                        input_data_hash: str, session_id: str) -> Dict:
        if partner_id not in self.integrations:
            return {"error": "Partner not found"}

        if session_id not in self.auth_sessions:
            return {"error": "Invalid session"}

        partner = self.integrations[partner_id]
        session = self.auth_sessions[session_id]

        if session["partner_id"] != partner_id:
            return {"error": "Session mismatch"}

        tier_complexity_factor = {1: 1.0, 2: 0.95, 3: 0.90, 4: 0.85, 5: 0.80}
        adjusted_complexity = complexity * tier_complexity_factor.get(partner["tier"], 1.0)

        phi_c_workload = partner["phi_c_base"] * (1.0 - adjusted_complexity * 0.1) * (1.0 + session["humility"] * 0.1)
        phi_c_workload = max(GHOST, min(GAP_SOVEREIGN, phi_c_workload))

        output_humility = session["humility"] * (1.0 - adjusted_complexity * 0.05)

        if output_humility < GHOST:
            partner["rejected_workloads"] += 1
            return {"status": "rejected", "reason": f"Output humility {output_humility:.4f} < Ghost"}

        seal_input = (
            f"safecore_v3_exp_{partner_id}_{workload_type}_{input_data_hash}_"
            f"{phi_c_workload:.6f}_{datetime.now(timezone.utc).isoformat()}"
        )
        seal = hashlib.sha3_256(seal_input.encode()).hexdigest()

        partner["verified_workloads"] += 1
        self.seals.append({
            "seal": seal,
            "partner": partner_id,
            "workload": workload_type,
            "phi_c": phi_c_workload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "status": "computed",
            "partner": partner_id,
            "workload": workload_type,
            "phi_c": phi_c_workload,
            "output_humility": output_humility,
            "seal": seal,
        }

    def cross_substrate_test(self, partner_a: str, partner_b: str, test_type: str) -> Dict:
        if partner_a not in self.integrations or partner_b not in self.integrations:
            return {"error": "Partner not found"}

        pa = self.integrations[partner_a]
        pb = self.integrations[partner_b]

        phi_c_bridge = (pa["phi_c_base"] + pb["phi_c_base"]) / 2 * (1.0 + random.random() * 0.05)
        phi_c_bridge = max(GHOST, min(GAP_SOVEREIGN, phi_c_bridge))

        ghost_compatible = phi_c_bridge > GHOST
        loopseal_compatible = phi_c_bridge > LOOPSEAL
        gap_compatible = phi_c_bridge < GAP_SOVEREIGN

        passed = ghost_compatible and loopseal_compatible and gap_compatible

        if passed:
            pa["cross_tests_passed"] += 1
            pb["cross_tests_passed"] += 1
        else:
            pa["cross_tests_failed"] += 1
            pb["cross_tests_failed"] += 1

        seal_input = (
            f"cross_substrate_{partner_a}_{partner_b}_{test_type}_"
            f"{phi_c_bridge:.6f}_{datetime.now(timezone.utc).isoformat()}"
        )
        seal = hashlib.sha3_256(seal_input.encode()).hexdigest()

        self.cross_substrate_tests.append({
            "seal": seal,
            "partner_a": partner_a,
            "partner_b": partner_b,
            "test_type": test_type,
            "phi_c_bridge": phi_c_bridge,
            "passed": passed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "status": "passed" if passed else "failed",
            "partner_a": partner_a,
            "partner_b": partner_b,
            "test_type": test_type,
            "phi_c_bridge": phi_c_bridge,
            "invariants": {
                "ghost": ghost_compatible,
                "loopseal": loopseal_compatible,
                "gap": gap_compatible,
            },
            "seal": seal,
        }

    def get_sdk_statistics(self) -> Dict:
        total_partners = len(self.integrations)
        authenticated = sum(1 for p in self.integrations.values() if p["auth_timestamp"] is not None)
        total_workloads = sum(p["verified_workloads"] + p["rejected_workloads"] for p in self.integrations.values())
        total_verified = sum(p["verified_workloads"] for p in self.integrations.values())

        phi_c_values = [p["phi_c_base"] for p in self.integrations.values()]

        tier_stats = {}
        for tier in [1, 2, 3, 4, 5]:
            tier_partners = [p for p in self.integrations.values() if p["tier"] == tier]
            if tier_partners:
                tier_stats[tier] = {
                    "count": len(tier_partners),
                    "avg_phi_c": ((sum([p["phi_c_base"] for p in tier_partners]) / len(tier_partners) if tier_partners else 0.0) / len(tier_partners) if tier_partners else 0.0),
                    "authenticated": sum(1 for p in tier_partners if p["auth_timestamp"] is not None),
                }

        category_stats = {}
        for cat in ["gigante", "enterprise", "startup", "lab", "opensource", "governo", "ong", "consorcio", "academia"]:
            cat_partners = [p for p in self.integrations.values() if p["category"] == cat]
            if cat_partners:
                category_stats[cat] = {
                    "count": len(cat_partners),
                    "avg_phi_c": ((sum([p["phi_c_base"] for p in tier_partners]) / len(tier_partners) if tier_partners else 0.0) / len(tier_partners) if tier_partners else 0.0),
                }

        type_stats = {}
        for t in ["tech", "gov", "ngo", "consortium", "academia", "community"]:
            type_partners = [p for p in self.integrations.values() if p["type"] == t]
            if type_partners:
                type_stats[t] = {
                    "count": len(type_partners),
                    "avg_phi_c": ((sum([p["phi_c_base"] for p in tier_partners]) / len(tier_partners) if tier_partners else 0.0) / len(tier_partners) if tier_partners else 0.0),
                }

        region_stats = {}
        for p in self.integrations.values():
            r = p["region"]
            if r not in region_stats:
                region_stats[r] = {"count": 0, "phi_c_sum": 0.0}
            region_stats[r]["count"] += 1
            region_stats[r]["phi_c_sum"] += p["phi_c_base"]

        for r in region_stats:
            region_stats[r]["avg_phi_c"] = region_stats[r]["phi_c_sum"] / region_stats[r]["count"]
            del region_stats[r]["phi_c_sum"]

        cross_tests = self.cross_substrate_tests
        cross_passed = sum(1 for t in cross_tests if t["passed"])
        cross_total = len(cross_tests)

        return {
            "total_partners": total_partners,
            "authenticated": authenticated,
            "pending_auth": total_partners - authenticated,
            "total_workloads": total_workloads,
            "verified_workloads": total_verified,
            "rejected_workloads": total_workloads - total_verified,
            "global_success_rate": total_verified / total_workloads if total_workloads > 0 else 0.0,
            "avg_phi_c": (sum(phi_c_values) / len(phi_c_values) if phi_c_values else 0.0),
            "min_phi_c": min(phi_c_values),
            "max_phi_c": max(phi_c_values),
            "std_phi_c": 0.0,
            "total_seals": len(self.seals),
            "tier_stats": tier_stats,
            "category_stats": category_stats,
            "type_stats": type_stats,
            "region_stats": region_stats,
            "cross_tests_total": cross_total,
            "cross_tests_passed": cross_passed,
            "cross_tests_failed": cross_total - cross_passed,
            "cross_success_rate": cross_passed / cross_total if cross_total > 0 else 0.0,
        }
