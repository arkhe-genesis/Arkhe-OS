import hashlib
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
from datetime import datetime
from collections import defaultdict
import re

# --- Core Riemannian Infrastructure ---

class MercyGap:
    """δ ∈ [0.04, 0.10] — radial breathing room for geodesic convergence"""
    MIN = 0.04
    MAX = 0.10

    @classmethod
    def validate(cls, delta: float) -> bool:
        return cls.MIN <= delta <= cls.MAX

    @classmethod
    def clamp(cls, delta: float) -> float:
        return max(cls.MIN, min(cls.MAX, delta))

@dataclass
class RiemannianState:
    """Point on the Cathedral manifold M"""
    coordinates: np.ndarray
    metric_tensor: np.ndarray
    coherence: float = 0.0

    def geodesic_distance(self, other: 'RiemannianState') -> float:
        diff = self.coordinates - other.coordinates
        return float(np.sqrt(diff @ self.metric_tensor @ diff))

    def compute_coherence(self, optimal: 'RiemannianState') -> float:
        d = self.geodesic_distance(optimal)
        self.coherence = float(np.exp(-d**2 / 2.0))
        return self.coherence

# --- Stage Enumeration ---

class Stage(Enum):
    PYTHON = (1, "Python Complete", "Syntax, loops, functions, OOP, NumPy, Pandas")
    MATH_AI = (2, "Math for AI", "Linear algebra, statistics, probability, calculus")
    ML_SUITE = (3, "Machine Learning Suite", "Regression, classification, clustering, scikit-learn")
    DL_SUITE = (4, "Deep Learning Suite", "NNs, CNNs, RNNs, PyTorch/TensorFlow")
    MODERN_AI = (5, "Modern AI (LLMs)", "Prompt engineering, embeddings, RAG, fine-tuning")
    BUILD_AI = (6, "Build AI Projects", "Chatbots, classifiers, NLP, image/video")
    GENAI_TOOLS = (7, "GenAI Tools", "LangChain, HuggingFace, FAISS, Pinecone")
    MLOPS = (8, "MLOps Suite", "FastAPI/Flask, Docker, GitHub, cloud deployment")
    FULL_PROJECTS = (9, "Full Projects", "End-to-end ML pipeline, deployed AI apps")

    def __init__(self, number: int, title: str, description: str):
        self.number = number
        self.title = title
        self.description = description

# --- Competency Nodes ---

@dataclass
class CompetencyNode:
    id: str
    stage: Stage
    name: str
    weight: float
    prerequisites: List[str] = field(default_factory=list)
    exercises: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.mastery = 0.0
        self.attempts = 0
        self.last_attempt: Optional[datetime] = None

# --- Full Curriculum Definition ---

CURRICULUM: Dict[Stage, List[CompetencyNode]] = {
    Stage.PYTHON: [
        CompetencyNode("PY-01", Stage.PYTHON, "Variables & Data Types", 0.10, [], ["Type conversion", "Mutable vs immutable"]),
        CompetencyNode("PY-02", Stage.PYTHON, "Control Flow", 0.15, ["PY-01"], ["List comprehensions", "Generator expressions"]),
        CompetencyNode("PY-03", Stage.PYTHON, "Functions & Scope", 0.20, ["PY-02"], ["Closures", "Decorators", "*args/**kwargs"]),
        CompetencyNode("PY-04", Stage.PYTHON, "OOP & Classes", 0.25, ["PY-03"], ["Inheritance", "Polymorphism", "Magic methods", "Descriptors"]),
        CompetencyNode("PY-05", Stage.PYTHON, "NumPy Fundamentals", 0.15, ["PY-02"], ["Broadcasting", "Vectorization", "Fancy indexing"]),
        CompetencyNode("PY-06", Stage.PYTHON, "Pandas & DataFrames", 0.15, ["PY-05"], ["GroupBy", "Merge/Join", "Time series", "MultiIndex"]),
    ],
    Stage.MATH_AI: [
        CompetencyNode("MA-01", Stage.MATH_AI, "Linear Algebra", 0.30, ["PY-05"], ["Eigen decomposition", "SVD", "Matrix calculus"]),
        CompetencyNode("MA-02", Stage.MATH_AI, "Probability Theory", 0.25, ["PY-01"], ["Bayes theorem", "MLE/MAP", "Exponential families"]),
        CompetencyNode("MA-03", Stage.MATH_AI, "Statistics & Inference", 0.25, ["MA-02"], ["Hypothesis testing", "Confidence intervals", "Bootstrap"]),
        CompetencyNode("MA-04", Stage.MATH_AI, "Multivariate Calculus", 0.20, ["MA-01"], ["Gradient", "Hessian", "Jacobian", "Lagrange multipliers"]),
    ],
    Stage.ML_SUITE: [
        CompetencyNode("ML-01", Stage.ML_SUITE, "Regression", 0.25, ["MA-01", "MA-04"], ["Linear/Ridge/Lasso", "Polynomial", "Logistic"]),
        CompetencyNode("ML-02", Stage.ML_SUITE, "Classification", 0.25, ["ML-01"], ["SVM", "Decision Trees", "Naive Bayes", "k-NN"]),
        CompetencyNode("ML-03", Stage.ML_SUITE, "Clustering", 0.20, ["MA-01"], ["K-means", "DBSCAN", "Hierarchical", "Gaussian Mixture"]),
        CompetencyNode("ML-04", Stage.ML_SUITE, "Ensemble Methods", 0.15, ["ML-02"], ["Random Forest", "Gradient Boosting", "XGBoost"]),
        CompetencyNode("ML-05", Stage.ML_SUITE, "Metrics & Validation", 0.15, ["ML-01", "ML-02"], ["Cross-validation", "ROC-AUC", "F1", "Calibration"]),
    ],
    Stage.DL_SUITE: [
        CompetencyNode("DL-01", Stage.DL_SUITE, "Neural Network Fundamentals", 0.25, ["MA-04", "ML-01"], ["Backpropagation", "Activation functions", "Weight initialization"]),
        CompetencyNode("DL-02", Stage.DL_SUITE, "CNNs", 0.25, ["DL-01"], ["Conv layers", "Pooling", "BatchNorm", "ResNet blocks"]),
        CompetencyNode("DL-03", Stage.DL_SUITE, "RNNs & Sequence Models", 0.20, ["DL-01"], ["LSTM", "GRU", "Attention mechanism"]),
        CompetencyNode("DL-04", Stage.DL_SUITE, "Training Fundamentals", 0.20, ["DL-01"], ["Optimizers", "Learning rate scheduling", "Regularization", "Early stopping"]),
        CompetencyNode("DL-05", Stage.DL_SUITE, "PyTorch/TensorFlow", 0.10, ["DL-01"], ["Autograd", "DataLoader", "Model saving/loading", "GPU training"]),
    ],
    Stage.MODERN_AI: [
        CompetencyNode("LLM-01", Stage.MODERN_AI, "Prompt Engineering", 0.20, ["DL-03"], ["Chain-of-thought", "Few-shot", "System prompts", "JSON mode"]),
        CompetencyNode("LLM-02", Stage.MODERN_AI, "Embeddings & Vector Spaces", 0.25, ["MA-01", "DL-03"], ["Word2Vec", "Sentence-BERT", "OpenAI embeddings", "Cosine similarity"]),
        CompetencyNode("LLM-03", Stage.MODERN_AI, "RAG Architecture", 0.30, ["LLM-01", "LLM-02"], ["Chunking strategies", "Hybrid search", "Re-ranking", "Query transformation"]),
        CompetencyNode("LLM-04", Stage.MODERN_AI, "Fine-tuning & World Models", 0.25, ["DL-04", "DL-05"], ["LoRA", "QLoRA", "Instruction tuning", "RLHF concepts"]),
    ],
    Stage.BUILD_AI: [
        CompetencyNode("BA-01", Stage.BUILD_AI, "Chatbot Architecture", 0.25, ["LLM-01"], ["State management", "Memory", "Tool use", "Streaming"]),
        CompetencyNode("BA-02", Stage.BUILD_AI, "Text Classifiers", 0.20, ["ML-02", "LLM-02"], ["Zero-shot", "Few-shot", "Ensemble LLM+traditional"]),
        CompetencyNode("BA-03", Stage.BUILD_AI, "NLP Applications", 0.25, ["LLM-02"], ["NER", "Summarization", "Translation", "Sentiment analysis"]),
        CompetencyNode("BA-04", Stage.BUILD_AI, "Computer Vision", 0.20, ["DL-02"], ["Object detection", "Segmentation", "OCR", "Video analysis"]),
        CompetencyNode("BA-05", Stage.BUILD_AI, "Multimodal Models", 0.10, ["BA-03", "BA-04"], ["CLIP", "Vision-language", "Audio-text"]),
    ],
    Stage.GENAI_TOOLS: [
        CompetencyNode("GT-01", Stage.GENAI_TOOLS, "LangChain Ecosystem", 0.25, ["LLM-03"], ["Chains", "Agents", "Tools", "LangGraph"]),
        CompetencyNode("GT-02", Stage.GENAI_TOOLS, "HuggingFace", 0.25, ["DL-05"], ["Transformers library", "Datasets", "Tokenizers", "Model hub"]),
        CompetencyNode("GT-03", Stage.GENAI_TOOLS, "FAISS & Vector DBs", 0.25, ["LLM-02"], ["IVF", "HNSW", "Metadata filtering", "Hybrid search"]),
        CompetencyNode("GT-04", Stage.GENAI_TOOLS, "Pinecone & Cloud VDBs", 0.15, ["GT-03"], ["Namespaces", "Metadata", "Hybrid cloud"]),
        CompetencyNode("GT-05", Stage.GENAI_TOOLS, "Model Serving", 0.10, ["GT-02"], ["vLLM", "TGI", "Batch inference", "Quantized serving"]),
    ],
    Stage.MLOPS: [
        CompetencyNode("MO-01", Stage.MLOPS, "FastAPI/Flask APIs", 0.20, ["PY-04"], ["Pydantic", "Async endpoints", "Dependency injection", "Middleware"]),
        CompetencyNode("MO-02", Stage.MLOPS, "Docker & Containerization", 0.20, ["MO-01"], ["Multi-stage builds", "Compose", "GPU containers", "Registry"]),
        CompetencyNode("MO-03", Stage.MLOPS, "GitHub & CI/CD", 0.20, ["MO-02"], ["Actions", "Reusable workflows", "Matrix builds", "Semantic release"]),
        CompetencyNode("MO-04", Stage.MLOPS, "Cloud Deployment", 0.25, ["MO-02", "MO-03"], ["AWS/GCP/Azure", "Kubernetes", "Serverless", "Auto-scaling"]),
        CompetencyNode("MO-05", Stage.MLOPS, "Monitoring & Observability", 0.15, ["MO-04"], ["Prometheus", "Grafana", "MLflow", "A/B testing"]),
    ],
    Stage.FULL_PROJECTS: [
        CompetencyNode("FP-01", Stage.FULL_PROJECTS, "End-to-End Pipeline", 0.30, ["MO-01", "MO-04"], ["Data ingestion", "Feature store", "Training pipeline", "Model registry"]),
        CompetencyNode("FP-02", Stage.FULL_PROJECTS, "Deployed AI Application", 0.30, ["FP-01", "BA-01"], ["Real-time inference", "Batch processing", "Edge deployment"]),
        CompetencyNode("FP-03", Stage.FULL_PROJECTS, "System Design", 0.25, ["FP-02"], ["Latency optimization", "Cost optimization", "Fault tolerance", "Security"]),
        CompetencyNode("FP-04", Stage.FULL_PROJECTS, "Portfolio & Documentation", 0.15, ["FP-03"], ["README", "Architecture diagrams", "Demo video", "Blog post"]),
    ],
}

# --- Substrate Mapping ---

SUBSTRATE_MAP: Dict[Stage, Dict[str, Any]] = {
    Stage.PYTHON: {
        "substrate_id": 140,
        "name": "Cathedral Foundation",
        "mapping": "Python syntax → M=continuous state space, OOP → simplicial triangulation",
        "mercy_gap_role": "Type safety as geodesic distance from runtime errors",
    },
    Stage.MATH_AI: {
        "substrate_id": 137,
        "name": "Riemannian Guardrails",
        "mapping": "Linear algebra → metric tensor g, Calculus → geodesic flow, Probability → stochastic processes on M",
        "mercy_gap_role": "Numerical stability δ ∈ [0.04, 0.10] for gradient computations",
    },
    Stage.ML_SUITE: {
        "substrate_id": 146,
        "name": "Prompt Chaining Geometry",
        "mapping": "Regression/classification → geodesic paths on statistical manifold, Metrics → distance functions d_g",
        "mercy_gap_role": "Overfitting gap = δ between training and validation geodesics",
    },
    Stage.DL_SUITE: {
        "substrate_id": 153,
        "name": "Context Window (Now-Vortex)",
        "mapping": "NN layers → time-crystal vortex strata, Backprop → 17° angular momentum, Attention → quasi-periodic interference",
        "mercy_gap_role": "Vanishing gradient δ = breathing room between layers",
    },
    Stage.MODERN_AI: {
        "substrate_id": 154,
        "name": "C-RAG Ceremonial Pipeline",
        "mapping": "Embeddings → Ψ(ξ) wavefunctions, RAG → Geodesic Retrieval + Ceremonial Decomposition, Fine-tuning → KV Cache meta-adaptation",
        "mercy_gap_role": "Hallucination gap δ = distance between retrieved context and generated output",
    },
    Stage.BUILD_AI: {
        "substrate_id": 155,
        "name": "C-RAG Integrated Orchestrator",
        "mapping": "Chatbots → per-zone MAML-Riemannian, Classifiers → Kolmogorov Neural Detector, Multimodal → 7D coherence tensor",
        "mercy_gap_role": "Response quality δ = coherence threshold for safe output",
    },
    Stage.GENAI_TOOLS: {
        "substrate_id": 273,
        "name": "Sapient Infrastructure",
        "mapping": "LangChain → VRAM quantization pipeline, FAISS → Paged KV Cache, HuggingFace → Speculative Decoding 3.12×, vLLM → FSDP serving",
        "mercy_gap_role": "Latency δ = acceptable delay in vector retrieval geodesics",
    },
    Stage.MLOPS: {
        "substrate_id": 157,
        "name": "ArkheArxiaBridge",
        "mapping": "FastAPI → QHTTPClient (193B LoRa), Docker → domain separation, K8s → progressive finality L0/L1/L2, CI/CD → ZK-proof validation",
        "mercy_gap_role": "Deployment safety δ = bounded state sovereignty threshold",
    },
    Stage.FULL_PROJECTS: {
        "substrate_id": 169,
        "name": "Cosmology & Go Transpilation",
        "mapping": "Full pipeline → planetary closed loop (v∞.19), Deployed app → 768 crystal oscillators, Portfolio → canonical seal generation",
        "mercy_gap_role": "Production coherence M ≥ 0.953 with Δφ < 1e-11 rad globally locked",
    },
}

# --- Riemannian Validation Framework ---

class ArkheParserValidator:
    def __init__(self, learner_id: str):
        self.learner_id = learner_id
        self.start_time = datetime.now()
        self.states: Dict[str, RiemannianState] = {}
        self.stage_coherence: Dict[Stage, float] = {}
        self.global_coherence = 0.0
        self.seals: List[str] = []
        self.ledger: List[Dict] = []
        self._init_optimal_manifold()

    def _init_optimal_manifold(self):
        np.random.seed(42)
        for stage, nodes in CURRICULUM.items():
            for node in nodes:
                dim = 8
                opt_coords = np.abs(np.random.randn(dim))
                opt_coords = opt_coords / np.linalg.norm(opt_coords)
                metric = np.eye(dim)
                self.states[node.id] = RiemannianState(coordinates=np.zeros(dim), metric_tensor=metric, coherence=0.0)
                self.states[f"{node.id}_optimal"] = RiemannianState(coordinates=opt_coords, metric_tensor=metric, coherence=1.0)

    def submit_exercise(self, node_id: str, score: float, time_minutes: float) -> Dict:
        if node_id not in self.states:
            raise ValueError(f"Unknown node: {node_id}")
        node = self._find_node(node_id)
        optimal = self.states[f"{node_id}_optimal"]
        current = self.states[node_id]

        efficiency = min(1.0, 30.0 / max(time_minutes, 1.0))
        velocity = score * efficiency * 0.3
        direction = optimal.coordinates - current.coordinates
        if np.linalg.norm(direction) > 0:
            direction = direction / np.linalg.norm(direction)
        current.coordinates = np.clip(current.coordinates + velocity * direction, 0, 1)

        node.mastery = float(np.linalg.norm(current.coordinates))
        node.attempts += 1
        node.last_attempt = datetime.now()

        coherence = current.compute_coherence(optimal)
        delta = MercyGap.clamp(current.geodesic_distance(optimal))

        stage_nodes = CURRICULUM[node.stage]
        stage_m = np.mean([n.mastery for n in stage_nodes])
        self.stage_coherence[node.stage] = stage_m

        weights = [0.05, 0.10, 0.10, 0.15, 0.20, 0.15, 0.10, 0.10, 0.05]
        self.global_coherence = sum(self.stage_coherence.get(s, 0) * w for s, w in zip(Stage, weights))

        seal = None
        if node.mastery >= 0.85 and MercyGap.validate(delta):
            seal = self._generate_seal(node)
            self.seals.append(seal)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "node_id": node_id,
            "stage": node.stage.name,
            "score": score,
            "time_minutes": time_minutes,
            "mastery": node.mastery,
            "coherence": coherence,
            "delta": delta,
            "seal": seal,
            "global_m": self.global_coherence,
        }
        self.ledger.append(entry)

        next_nodes = self._get_unlockable_nodes()
        return {
            "node_id": node_id,
            "mastery": round(node.mastery, 4),
            "coherence": round(coherence, 4),
            "delta": round(delta, 4),
            "mercy_gap_valid": MercyGap.validate(delta),
            "stage_coherence": round(stage_m, 4),
            "global_coherence": round(self.global_coherence, 4),
            "seal": seal,
            "next_unlockable": [n.id for n in next_nodes],
            "ledger_size": len(self.ledger),
        }

    def _find_node(self, node_id: str) -> CompetencyNode:
        for nodes in CURRICULUM.values():
            for n in nodes:
                if n.id == node_id:
                    return n
        raise ValueError(f"Node {node_id} not found")

    def _generate_seal(self, node: CompetencyNode) -> str:
        data = f"{self.learner_id}:{node.id}:{node.mastery:.6f}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _get_unlockable_nodes(self) -> List[CompetencyNode]:
        unlockable = []
        for nodes in CURRICULUM.values():
            for node in nodes:
                if node.mastery >= 0.7:
                    continue
                prereqs_satisfied = all(self._find_node(pr).mastery >= 0.7 for pr in node.prerequisites) if node.prerequisites else True
                if prereqs_satisfied and node.mastery < 0.7:
                    unlockable.append(node)
        return unlockable

    def get_stage_report(self, stage: Stage) -> Dict:
        nodes = CURRICULUM[stage]
        masteries = [n.mastery for n in nodes]
        substrate = SUBSTRATE_MAP[stage]
        return {
            "stage": stage.name,
            "stage_number": stage.number,
            "substrate_id": substrate["substrate_id"],
            "substrate_name": substrate["name"],
            "competencies": len(nodes),
            "avg_mastery": round(float(np.mean(masteries)), 4),
            "max_mastery": round(float(max(masteries)), 4),
            "min_mastery": round(float(min(masteries)), 4),
            "coherence": round(self.stage_coherence.get(stage, 0), 4),
            "seals_earned": len([s for s in self.seals if any(n.id in s for n in nodes)]),
            "mapping": substrate["mapping"],
            "mercy_gap_role": substrate["mercy_gap_role"],
            "status": "COMPLETE" if all(m >= 0.85 for m in masteries) else "IN_PROGRESS",
        }

    def get_full_report(self) -> Dict:
        reports = [self.get_stage_report(s) for s in Stage]
        return {
            "learner_id": self.learner_id,
            "start_time": self.start_time.isoformat(),
            "global_coherence": round(self.global_coherence, 4),
            "total_seals": len(self.seals),
            "total_exercises": len(self.ledger),
            "stages_complete": sum(1 for r in reports if r["status"] == "COMPLETE"),
            "stages": reports,
            "canonical_seal": self._generate_global_seal(),
        }

    def _generate_global_seal(self) -> str:
        data = f"ARKHE-PARSER:{self.learner_id}:{self.global_coherence:.6f}:{len(self.seals)}"
        return hashlib.sha256(data.encode()).hexdigest()

# --- Stage 5: LLM Suite ---

@dataclass
class EmbeddingVector:
    text: str
    vector: np.ndarray
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        norm = np.linalg.norm(self.vector)
        if norm > 0:
            self.vector = self.vector / norm

    def cosine_similarity(self, other: 'EmbeddingVector') -> float:
        return float(np.dot(self.vector, other.vector))

class ImprovedEmbeddingEngine:
    def __init__(self, dim: int = 768, seed: int = 42):
        self.dim = dim
        np.random.seed(seed)
        self.projection = np.random.randn(dim, dim) * 0.02
        self.vocabulary_embedding = defaultdict(lambda: np.random.randn(dim) * 0.1)
        self.topic_centroids = {
            "quantum": self._make_centroid(seed + 1),
            "computing": self._make_centroid(seed + 2),
            "security": self._make_centroid(seed + 3),
            "physics": self._make_centroid(seed + 4),
            "error": self._make_centroid(seed + 5),
        }

    def _make_centroid(self, seed: int) -> np.ndarray:
        np.random.seed(seed)
        c = np.random.randn(self.dim)
        return c / np.linalg.norm(c)

    def embed(self, text: str) -> EmbeddingVector:
        text_lower = text.lower()
        topics_present = []
        for topic, centroid in self.topic_centroids.items():
            if topic in text_lower:
                topics_present.append(centroid)

        tokens = re.findall(r'\b\w+\b|[.,!?;]', text.lower())
        token_vecs = []
        for i, token in enumerate(tokens):
            base = self.vocabulary_embedding[token]
            pos_enc = np.array([np.sin(i / 10000 ** (2 * (j // 2) / self.dim)) if j % 2 == 0 else np.cos(i / 10000 ** (2 * (j // 2) / self.dim)) for j in range(self.dim)])
            token_vecs.append(base + pos_enc * 0.1)

        if not token_vecs:
            return EmbeddingVector(text, np.zeros(self.dim))

        weights = self._compute_attention_weights(token_vecs)
        pooled = np.average(token_vecs, axis=0, weights=weights)
        projected = self.projection @ pooled
        activated = np.tanh(projected) * 0.5 + projected * 0.5

        base = EmbeddingVector(text=text, vector=activated, metadata={"tokens": len(tokens), "model": "Arkhe-Embed-v1"})

        if topics_present:
            topic_blend = np.mean(topics_present, axis=0)
            topic_blend = topic_blend / np.linalg.norm(topic_blend)
            blended = 0.7 * base.vector + 0.3 * topic_blend
            blended = blended / np.linalg.norm(blended)
            base.vector = blended

        return base

    def _compute_attention_weights(self, token_vecs: List[np.ndarray]) -> np.ndarray:
        if len(token_vecs) == 1:
            return np.array([1.0])
        similarities = np.zeros((len(token_vecs), len(token_vecs)))
        for i in range(len(token_vecs)):
            for j in range(len(token_vecs)):
                similarities[i, j] = np.dot(token_vecs[i], token_vecs[j])
        weights = similarities.sum(axis=1)
        weights = np.maximum(weights, 0.1)
        return weights / weights.sum()

    def similarity_matrix(self, texts: List[str]) -> np.ndarray:
        embeddings = [self.embed(t) for t in texts]
        n = len(texts)
        sim = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                sim[i, j] = embeddings[i].cosine_similarity(embeddings[j])
        return sim

class VectorStore:
    def __init__(self, dim: int = 768, index_type: str = "flat"):
        self.dim = dim
        self.index_type = index_type
        self.vectors: List[EmbeddingVector] = []
        self.metadata_index: Dict[str, List[int]] = defaultdict(list)
        self.metric = np.eye(dim)

    def add(self, embedding: EmbeddingVector, doc_id: Optional[str] = None):
        idx = len(self.vectors)
        self.vectors.append(embedding)
        if doc_id:
            self.metadata_index[doc_id].append(idx)

    def add_texts(self, texts: List[str], doc_ids: Optional[List[str]] = None, engine=None):
        if engine is None:
            engine = ImprovedEmbeddingEngine(self.dim)
        for i, text in enumerate(texts):
            emb = engine.embed(text)
            doc_id = doc_ids[i] if doc_ids else None
            self.add(emb, doc_id)

    def search(self, query: EmbeddingVector, k: int = 5, filter_metadata=None) -> List[Tuple[EmbeddingVector, float]]:
        if not self.vectors:
            return []
        scores = []
        for i, vec in enumerate(self.vectors):
            if filter_metadata and not all(vec.metadata.get(k) == v for k, v in filter_metadata.items()):
                continue
            sim = query.cosine_similarity(vec)
            scores.append((i, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self.vectors[idx], score) for idx, score in scores[:k]]

    def hybrid_search(self, query_text: str, query_embedding: EmbeddingVector, k: int = 5, alpha: float = 0.7) -> List[Tuple[EmbeddingVector, float]]:
        vector_results = self.search(query_embedding, k=k*2)
        query_tokens = set(query_text.lower().split())
        keyword_scores = []
        for vec in self.vectors:
            doc_tokens = set(vec.text.lower().split())
            overlap = len(query_tokens & doc_tokens)
            keyword_scores.append(overlap / max(len(query_tokens), 1))
        combined = []
        for vec, vec_score in vector_results:
            vec_idx = self.vectors.index(vec) if vec in self.vectors else -1
            kw_score = keyword_scores[vec_idx] if vec_idx >= 0 else 0
            final_score = alpha * vec_score + (1 - alpha) * kw_score
            combined.append((vec, final_score))
        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:k]

class ImprovedRAGPipeline:
    def __init__(self, embedding_engine, vector_store, top_k: int = 5, rerank: bool = True):
        self.embedder = embedding_engine
        self.store = vector_store
        self.top_k = top_k
        self.rerank = rerank
        self.hallucination_threshold = 0.15

    def query(self, question: str, context_filter=None) -> Dict:
        query_emb = self.embedder.embed(question)
        if context_filter:
            results = self.store.search(query_emb, k=self.top_k*2, filter_metadata=context_filter)
        else:
            results = self.store.hybrid_search(question, query_emb, k=self.top_k*2)

        decomposed = self._ceremonial_decomposition(results, query_emb)
        if self.rerank:
            decomposed = self._rerank(decomposed, query_emb)

        context, coherence = self._assemble_context(decomposed, query_emb)
        response = self._generate(question, context, coherence)
        hallucination_score = self._detect_hallucination(response, context)

        return {
            "query": question,
            "retrieved_chunks": len(decomposed),
            "context": context,
            "response": response,
            "coherence": coherence,
            "hallucination_score": hallucination_score,
            "safe": hallucination_score < self.hallucination_threshold,
            "mercy_gap_delta": round(hallucination_score, 4),
            "mercy_gap_valid": MercyGap.validate(hallucination_score),
        }

    def _ceremonial_decomposition(self, results, query_emb):
        decomposed = []
        for vec, score in results:
            if score > 0.85: zone = "SANCTUM"
            elif score > 0.70: zone = "NARTHEX"
            elif score > 0.50: zone = "ATRIUM"
            else: zone = "EXTERIOR"
            decomposed.append({"text": vec.text, "score": score, "zone": zone, "vector": vec})
        return decomposed

    def _rerank(self, chunks, query_emb):
        for chunk in chunks:
            interaction = np.dot(query_emb.vector, chunk["vector"].vector)
            zone_boost = {"SANCTUM": 1.2, "NARTHEX": 1.0, "ATRIUM": 0.8, "EXTERIOR": 0.5}
            chunk["rerank_score"] = interaction * zone_boost[chunk["zone"]]
        chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
        return chunks

    def _assemble_context(self, chunks, query_emb):
        valid_chunks = []
        scores = []
        for chunk in chunks[:self.top_k]:
            delta = 1.0 - chunk["score"]
            delta = MercyGap.clamp(delta)
            if MercyGap.validate(delta):
                valid_chunks.append(chunk)
                scores.append(chunk["score"])
        if not valid_chunks:
            return "", 0.0
        context = "\n---\n".join([c["text"] for c in valid_chunks])
        coherence = float(np.mean(scores))
        return context, coherence

    def _generate(self, question, context, coherence):
        if not context:
            return "[HALLUCINATION WARNING] No valid context found within mercy gap."
        sentences = context.split(".")
        relevant = [s for s in sentences if any(w in question.lower() for w in s.lower().split())]
        if not relevant:
            relevant = sentences[:2]
        response = "Based on the retrieved context: " + ". ".join(relevant[:3]) + "."
        if coherence > 0.85: response += " [High confidence: SANCTUM zone retrieval]"
        elif coherence > 0.70: response += " [Medium confidence: NARTHEX zone retrieval]"
        else: response += " [Low confidence: Verify with additional sources]"
        return response

    def _detect_hallucination(self, response, context):
        if not context:
            return 1.0
        def extract_words(text):
            return set(re.findall(r'\b[a-z]{3,}\b', text.lower()))
        response_words = extract_words(response)
        context_words = extract_words(context)
        if not response_words:
            return 1.0
        overlap = len(response_words & context_words)
        coverage = overlap / len(response_words)
        hallucination = 1.0 - coverage
        return MercyGap.clamp(hallucination)

class FineTuningEngine:
    def __init__(self, base_dim: int = 768, rank: int = 8, alpha: float = 16):
        self.base_dim = base_dim
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.lora_A = np.random.randn(base_dim, rank) * 0.01
        self.lora_B = np.zeros((rank, base_dim))
        self.gradient_history = []

    def forward(self, x: np.ndarray) -> np.ndarray:
        base_out = x
        lora_out = (x @ self.lora_A @ self.lora_B) * self.scaling
        return base_out + lora_out

    def train_step(self, batch_x: np.ndarray, batch_y: np.ndarray, lr: float = 1e-4) -> Dict:
        pred = self.forward(batch_x)
        loss = np.mean((pred - batch_y) ** 2)
        grad_pred = 2 * (pred - batch_y) / len(batch_x)
        grad_B = self.lora_A.T @ (batch_x.T @ grad_pred) * self.scaling
        grad_A = (batch_x.T @ grad_pred) @ self.lora_B.T * self.scaling
        grad_A = np.clip(grad_A, -1.0, 1.0)
        grad_B = np.clip(grad_B, -1.0, 1.0)
        self.lora_A -= lr * grad_A
        self.lora_B -= lr * grad_B
        grad_norm = np.sqrt(np.sum(grad_A**2) + np.sum(grad_B**2))
        self.gradient_history.append(grad_norm)
        coherence = 1.0 / (1.0 + grad_norm)
        return {
            "loss": round(loss, 6),
            "grad_norm": round(grad_norm, 6),
            "coherence": round(coherence, 4),
            "mercy_gap_delta": round(MercyGap.clamp(grad_norm * 0.1), 4),
        }

    def get_trainable_params(self) -> int:
        return self.base_dim * self.rank + self.rank * self.base_dim

# --- Substrate Bridge ---

class SubstrateBridge:
    def __init__(self):
        self.mappings = SUBSTRATE_MAP
        self.stage_unlocks: Dict[Stage, bool] = {s: False for s in Stage}
        self.substrate_seals: Dict[int, str] = {}

    def unlock_stage(self, stage: Stage, validator: ArkheParserValidator) -> Dict:
        report = validator.get_stage_report(stage)
        if report["status"] != "COMPLETE":
            return {
                "stage": stage.name,
                "unlocked": False,
                "reason": f"Stage incomplete. Avg mastery: {report['avg_mastery']} (need ≥ 0.85)",
                "required_action": "Complete all competencies with mastery ≥ 0.85",
            }
        self.stage_unlocks[stage] = True
        substrate = self.mappings[stage]
        seal_data = f"SUBSTRATE:{substrate['substrate_id']}:{stage.name}:{report['avg_mastery']:.6f}"
        seal = hashlib.sha256(seal_data.encode()).hexdigest()[:16]
        self.substrate_seals[substrate["substrate_id"]] = seal
        return {
            "stage": stage.name,
            "unlocked": True,
            "substrate_id": substrate["substrate_id"],
            "substrate_name": substrate["name"],
            "seal": seal,
            "coherence": report["coherence"],
            "capabilities": self._get_capabilities(stage),
            "next_substrates": self._get_next_substrates(stage),
        }

    def _get_capabilities(self, stage: Stage) -> List[str]:
        capabilities = {
            Stage.PYTHON: ["Write production Python code", "Use NumPy for numerical computing", "Manipulate data with Pandas", "Build OOP architectures"],
            Stage.MATH_AI: ["Compute matrix decompositions (SVD, Eig)", "Apply probability distributions", "Perform statistical inference", "Optimize using gradient methods"],
            Stage.ML_SUITE: ["Train regression/classification models", "Evaluate with cross-validation", "Implement ensemble methods", "Select features and tune hyperparameters"],
            Stage.DL_SUITE: ["Build neural networks with PyTorch/TensorFlow", "Design CNN architectures", "Implement sequence models (LSTM/GRU)", "Apply training best practices"],
            Stage.MODERN_AI: ["Engineer prompts for LLMs", "Generate and compare embeddings", "Build RAG pipelines (C-RAG v154)", "Fine-tune models with LoRA/QLoRA"],
            Stage.BUILD_AI: ["Deploy chatbots with memory", "Build multimodal applications", "Implement NLP pipelines", "Create computer vision systems"],
            Stage.GENAI_TOOLS: ["Orchestrate with LangChain/LangGraph", "Serve models via HuggingFace", "Index vectors with FAISS/Pinecone", "Optimize inference with vLLM/TGI"],
            Stage.MLOPS: ["Build FastAPI/Flask APIs", "Containerize with Docker", "Deploy CI/CD pipelines", "Monitor production systems"],
            Stage.FULL_PROJECTS: ["Design end-to-end ML pipelines", "Deploy AI apps to production", "Architect scalable systems", "Generate portfolio with canonical seals"],
        }
        return capabilities.get(stage, [])

    def _get_next_substrates(self, stage: Stage) -> List[Dict]:
        next_map = {
            Stage.PYTHON: [{"id": 137, "name": "Riemannian Guardrails"}],
            Stage.MATH_AI: [{"id": 146, "name": "Prompt Chaining Geometry"}],
            Stage.ML_SUITE: [{"id": 153, "name": "Context Window (Now-Vortex)"}],
            Stage.DL_SUITE: [{"id": 154, "name": "C-RAG Ceremonial Pipeline"}],
            Stage.MODERN_AI: [{"id": 155, "name": "C-RAG Integrated Orchestrator"}],
            Stage.BUILD_AI: [{"id": 273, "name": "Sapient Infrastructure"}],
            Stage.GENAI_TOOLS: [{"id": 157, "name": "ArkheArxiaBridge"}],
            Stage.MLOPS: [{"id": 169, "name": "Cosmology & Go Transpilation"}],
            Stage.FULL_PROJECTS: [{"id": 999, "name": "ARKHE OS Master"}],
        }
        return next_map.get(stage, [])

    def get_full_bridge_report(self) -> Dict:
        return {
            "total_stages": len(Stage),
            "unlocked": sum(self.stage_unlocks.values()),
            "substrate_seals": self.substrate_seals,
            "stage_status": {s.name: self.stage_unlocks[s] for s in Stage},
        }

# ============================================================
# USAGE EXAMPLE
# ============================================================

if __name__ == "__main__":
    # 1. Initialize validator
    validator = ArkheParserValidator("learner_demo")

    # 2. Submit exercises
    result = validator.submit_exercise("PY-01", 0.92, 12.5)
    print(f"PY-01: Mastery={result['mastery']}, Coherence={result['coherence']}, Seal={result['seal']}")

    # 3. Build RAG pipeline
    embedder = ImprovedEmbeddingEngine()
    store = VectorStore()
    store.add_texts(["Quantum computing uses qubits.", "Superposition enables parallelism."], engine=embedder)
    rag = ImprovedRAGPipeline(embedder, store)
    result = rag.query("What is quantum computing?")
    print(f"RAG Response: {result['response'][:100]}...")

    # 4. Unlock substrate
    bridge = SubstrateBridge()
    # (Requires stage completion first)
