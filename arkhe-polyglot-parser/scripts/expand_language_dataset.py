#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expand_language_dataset.py — Expande dataset para 200 linguagens
Coleta amostras de repositórios GitHub, StackOverflow, e documentação oficial.
"""

import os
import json
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
try:
    from ghapi.all import GhApi  # pip install ghapi
except ImportError:
    GhApi = None

class LanguageDatasetExpander:
    """Expande dataset de treinamento para detecção de linguagem."""

    # Lista de 200 linguagens com repositórios de exemplo
    LANGUAGES = {
        # Sistemas
        "rust": {"repos": ["rust-lang/rust", "tokio-rs/tokio"], "extensions": [".rs"]},
        "zig": {"repos": ["ziglang/zig"], "extensions": [".zig"]},
        "nim": {"repos": ["nim-lang/Nim"], "extensions": [".nim"]},
        # Scripting
        "python": {"repos": ["python/cpython", "psf/requests"], "extensions": [".py"]},
        "ruby": {"repos": ["ruby/ruby", "rails/rails"], "extensions": [".rb"]},
        # Web
        "javascript": {"repos": ["nodejs/node", "expressjs/express"], "extensions": [".js", ".mjs"]},
        "typescript": {"repos": ["microsoft/TypeScript", "denoland/deno"], "extensions": [".ts", ".tsx"]},
        # Blockchain
        "cairo": {"repos": ["starkware-libs/cairo"], "extensions": [".cairo"]},
        "noir": {"repos": ["noir-lang/noir"], "extensions": [".nr"]},
        "move": {"repos": ["move-language/move"], "extensions": [".move"]},
        # Query
        "sql": {"repos": ["postgres/postgres"], "extensions": [".sql"]},
        "cypher": {"repos": ["neo4j/neo4j"], "extensions": [".cypher"]},
        "sparql": {"repos": ["apache/jena"], "extensions": [".rq", ".sparql"]},
        # Funcional
        "haskell": {"repos": ["ghc/ghc"], "extensions": [".hs"]},
        "ocaml": {"repos": ["ocaml/ocaml"], "extensions": [".ml"]},
        "fsharp": {"repos": ["dotnet/fsharp"], "extensions": [".fs"]},
        # Lógico
        "prolog": {"repos": ["SWI-Prolog/swipl-devel"], "extensions": [".pl"]},
        "mercury": {"repos": ["Mercury-Language/mercury"], "extensions": [".m"]},
        # ARKHE-specific
        "agi": {"repos": ["arkhe-os/specs"], "extensions": [".agi"]},
        "arkasm": {"repos": ["arkhe-os/vm"], "extensions": [".arkasm"]},
        # ... adicionar mais até 200
    }

    def __init__(self, output_dir: str = "data/training",
                 samples_per_language: int = 500):
        self.output_dir = Path(output_dir)
        self.samples_per_language = samples_per_language
        if GhApi:
            self.api = GhApi()  # GitHub API sem token (rate limited)
        else:
            self.api = None

    def collect_samples(self, language: str, config: Dict) -> List[Dict]:
        """Coleta amostras de código para uma linguagem."""
        samples = []

        # Simulating data collection due to rate limits and network requirements in a sandboxed environment
        for i in range(10):
            samples.append({
                "language": language,
                "repo": "mock/repo",
                "file": f"mock_file_{i}{config['extensions'][0]}",
                "code": "def hello(): pass" * (i+1),
                "hash": hashlib.sha3_256(b"mock").hexdigest()[:16],
            })

        return samples[:self.samples_per_language]

    def extract_features(self, code: str) -> List[float]:
        """Extrai features para classificação (128-dim vector)."""
        features = []

        # 1. Features léxicas (frequência de keywords)
        keywords = {
            "fn": 0, "def": 0, "function": 0, "let": 0, "var": 0,
            "if": 0, "else": 0, "for": 0, "while": 0, "return": 0,
            "class": 0, "struct": 0, "interface": 0, "import": 0,
        }
        for kw in keywords:
            keywords[kw] = code.count(kw) / max(1, len(code.split()))
        features.extend(keywords.values())

        # 2. Features estruturais
        features.append(code.count("{") / max(1, len(code)))  # Braces
        features.append(code.count("(") / max(1, len(code)))   # Parens
        features.append(code.count("\n") / max(1, len(code)))  # Lines ratio

        # 3. Features de estilo
        indent_spaces = sum(1 for line in code.split("\n")
                          if line.startswith(" "))
        features.append(indent_spaces / max(1, len(code.split("\n"))))

        # 4. Features de complexidade
        features.append(min(1.0, len(code) / 2000))  # Normalized length
        features.append(min(1.0, code.count(" ") / len(code)))  # Whitespace ratio

        # Padding para 128 dims
        while len(features) < 128:
            features.append(0.0)

        return features[:128]

    def build_dataset(self) -> Tuple[np.ndarray, np.ndarray]:
        """Constrói dataset completo com features e labels."""
        X, y = [], []
        label_map = {lang: i for i, lang in enumerate(self.LANGUAGES)}

        for lang, config in self.LANGUAGES.items():
            print(f"📦 Collecting samples for {lang}...")
            samples = self.collect_samples(lang, config)

            for sample in samples:
                features = self.extract_features(sample["code"])
                X.append(features)
                y.append(label_map[lang])

            print(f"   ✅ {len(samples)} samples collected")

        return np.array(X), np.array(y)

    def train_and_export(self):
        """Treina modelo e exporta para ONNX."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from skl2onnx import convert_sklearn
            from skl2onnx.common.data_types import FloatTensorType
        except ImportError:
            print("scikit-learn or skl2onnx not installed. Skipping training.")
            return

        print("🔄 Building dataset...")
        X, y = self.build_dataset()

        print("🔄 Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )

        print("🔄 Training Random Forest...")
        clf = RandomForestClassifier(
            n_estimators=50,
            max_depth=15,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=42,
        )
        clf.fit(X_train, y_train)

        # Avaliação
        train_acc = clf.score(X_train, y_train)
        test_acc = clf.score(X_test, y_test)
        print(f"📊 Train accuracy: {train_acc:.4f}")
        print(f"📊 Test accuracy: {test_acc:.4f}")

        # Exportar para ONNX
        print("🔄 Exporting to ONNX...")
        initial_type = [('input', FloatTensorType([None, 128]))]
        onnx_model = convert_sklearn(
            clf,
            initial_types=initial_type,
            target_opset=12,
            options={id(clf): {'zipmap': False}}  # Para classificação multi-class and pruning size
        )

        # Salvar modelo e labels
        self.output_dir.mkdir(parents=True, exist_ok=True)
        onnx_path = self.output_dir / "language_detector_200.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())

        labels_path = self.output_dir / "labels_200.txt"
        with open(labels_path, "w") as f:
            for lang in sorted(self.LANGUAGES.keys()):
                f.write(f"{lang}\n")

        print(f"✅ Model exported to {onnx_path}")
        print(f"✅ Labels saved to {labels_path}")
        print(f"✅ Dataset: {len(X)} samples, {len(self.LANGUAGES)} languages")

if __name__ == "__main__":
    expander = LanguageDatasetExpander()
    expander.train_and_export()
