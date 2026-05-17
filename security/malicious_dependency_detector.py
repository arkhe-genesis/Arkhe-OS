#!/usr/bin/env python3
"""
Substrato 232: Malicious Dependency Detector
Modelo treinado para identificação proativa de pacotes npm comprometidos
via análise comportamental, metadados, e padrões de publicação.
"""
import asyncio
import hashlib
import json
import time
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DependencyRiskAssessment:
    """Avaliação de risco de uma dependência."""
    package_name: str
    version: str
    risk_score: float  # 0.0 (seguro) a 1.0 (malicioso)
    risk_factors: Dict[str, float]  # fator → contribuição para risco
    is_malicious: bool
    confidence: float
    recommendations: List[str]
    temporal_seal: Optional[str] = None
    assessed_at: float = field(default_factory=time.time)

class MaliciousDependencyDetector:
    """
    Detector de dependências maliciosas com modelo treinado.

    Fontes de features para detecção:
    • Metadados do pacote: idade, publisher, download count, update frequency
    • Comportamento do código: imports suspeitos, eval/Function, network calls
    • Padrões de publicação: typosquatting, nome similar a pacotes populares
    • Histórico de segurança: vulnerabilidades reportadas, maintainer changes
    • Rede de dependências: dependências transitivas de alto risco

    Pipeline de detecção:
    1. Extrair features comportamentais e estáticas do pacote
    2. Normalizar features e aplicar modelo ensemble
    3. Calcular risk score e fatores contribuintes
    4. Gerar recomendações acionáveis
    5. Ancorar avaliação na TemporalChain
    """

    # Features extraídas para detecção
    BEHAVIORAL_FEATURES = [
        # Metadados do pacote
        "package_age_days",
        "publisher_account_age_days",
        "download_count_log",
        "update_frequency_days",
        "dependency_count",
        "dev_dependency_count",

        # Padrões de nomeação
        "typosquatting_score",  # Similaridade a pacotes populares
        "name_entropy",  # Entropia do nome (nomes aleatórios são suspeitos)
        "contains_numbers",  # Números em nomes podem indicar typosquatting

        # Comportamento do código (análise estática)
        "uses_eval",  # Uso de eval/Function
        "uses_child_process",  # Execução de comandos do sistema
        "uses_network_calls",  # Chamadas HTTP/HTTPS não justificadas
        "uses_file_system_write",  # Escrita em FS fora de padrões esperados
        "obfuscation_score",  # Código ofuscado/minificado

        # Histórico de segurança
        "known_vulnerabilities",
        "maintainer_changes_count",
        "suspicious_version_jumps",  # Ex: 1.0.0 → 9.9.9 sem changelog

        # Rede de dependências
        "transitive_deps_count",
        "high_risk_transitive_deps",
        "circular_dependency_depth"
    ]

    # Thresholds para classificação
    RISK_THRESHOLDS = {
        "low_risk": 0.30,
        "medium_risk": 0.60,
        "high_risk": 0.85,
        "block_threshold": 0.90
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        phi_bus=None,
        temporal_chain=None,
        package_registry=None
    ):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.registry = package_registry
        self.model_path = Path(model_path) if model_path else Path("/tmp/arkhe/models/malicious_deps")
        self.model_path.mkdir(parents=True, exist_ok=True)

        self._scaler = StandardScaler()
        self._isolation_forest: Optional[IsolationForest] = None
        self._classifier: Optional[RandomForestClassifier] = None
        self._popular_packages: set = set()  # Para detecção de typosquatting
        self._assessment_history: List[DependencyRiskAssessment] = []

        # Carregar modelo se disponível
        if (self.model_path / "malicious_dep_model.pkl").exists():
            self._load_model()

    async def assess_dependency(
        self,
        package_name: str,
        version: str,
        package_metadata: Optional[Dict] = None
    ) -> DependencyRiskAssessment:
        """
        Avalia risco de uma dependência específica.

        Args:
            package_name: Nome do pacote npm
            version: Versão a ser avaliada
            package_metadata: Metadados opcionais (se já disponíveis)

        Returns:
            DependencyRiskAssessment com score de risco e recomendações
        """
        # Extrair features do pacote
        features = await self._extract_features(package_name, version, package_metadata)

        # Normalizar features
        feature_vector = np.array([
            features.get(feat, 0.0) for feat in self.BEHAVIORAL_FEATURES
        ]).reshape(1, -1)

        # Prever com modelo ensemble
        if self._isolation_forest and self._classifier:
            try:
                feature_vector_scaled = self._scaler.transform(feature_vector)

                # Isolation Forest para detecção de novidades
                if_score = self._isolation_forest.score_samples(feature_vector_scaled)[0]
                if_normalized = 1 - (if_score + 1) / 2  # Mapear [-1, 0] → [0, 1]

                # Random Forest para classificação supervisionada
                rf_proba = self._classifier.predict_proba(feature_vector_scaled)[0][1]  # Prob de malicioso

                # Ensemble score (ponderado)
                risk_score = if_normalized * 0.4 + rf_proba * 0.6
            except Exception as e:
                logger.warning(f"Erro ao prever com modelo: {e}. Usando heurística.")
                risk_score = self._heuristic_risk_score(features)
        else:
            # Fallback: heurística simples se modelo não treinado
            risk_score = self._heuristic_risk_score(features)

        # Classificar risco
        is_malicious = risk_score >= self.RISK_THRESHOLDS["block_threshold"]
        confidence = max(risk_score, 1.0 - risk_score)  # Confiança na classificação

        # Identificar fatores de risco contribuintes
        risk_factors = self._identify_risk_factors(features, risk_score)

        # Gerar recomendações
        recommendations = self._generate_recommendations(risk_score, risk_factors)

        # Criar avaliação
        assessment = DependencyRiskAssessment(
            package_name=package_name,
            version=version,
            risk_score=float(risk_score),
            risk_factors=risk_factors,
            is_malicious=bool(is_malicious),
            confidence=float(confidence),
            recommendations=recommendations
        )

        # Ancorar na TemporalChain
        if self.temporal:
            assessment.temporal_seal = await self.temporal.anchor_event(
                "dependency_risk_assessed",
                {
                    "package": f"{package_name}@{version}",
                    "risk_score": risk_score,
                    "is_malicious": is_malicious,
                    "top_risk_factors": list(risk_factors.items())[:3],
                    "timestamp": time.time()
                }
            )

        self._assessment_history.append(assessment)

        # Publicar métrica
        if self.phi_bus:
            await self.phi_bus.publish_metric("dependency_risk_assessed", {
                "package": f"{package_name}@{version}",
                "risk_score": risk_score,
                "is_malicious": is_malicious
            })

        logger.info(
            f"🔍 Avaliação de risco: {package_name}@{version} | "
            f"Risk={risk_score:.3f} | "
            f"Malicious={is_malicious} | "
            f"Confidence={confidence:.3f}"
        )

        return assessment

    async def _extract_features(
        self,
        package_name: str,
        version: str,
        metadata: Optional[Dict]
    ) -> Dict[str, float]:
        """Extrai features comportamentais e estáticas do pacote."""
        features = {}

        # Obter metadados se não fornecidos
        if not metadata and self.registry:
            metadata_obj = await self.registry.fetch_package_metadata(package_name, version)
            if metadata_obj:
                metadata = {
                    "created_at": metadata_obj.cached_at,
                    "downloads": 1000,
                    "vulnerability_count": sum(metadata_obj.vulnerability_count.values()),
                }

        if metadata:
            # Metadados do pacote
            created = metadata.get("created_at")
            if created:
                features["package_age_days"] = (time.time() - created) / 86400
            else:
                features["package_age_days"] = 0.0

            publisher = metadata.get("publisher", {})
            features["publisher_account_age_days"] = publisher.get("account_age_days", 0.0)
            features["download_count_log"] = np.log1p(metadata.get("downloads", 0))

            versions = metadata.get("versions", {})
            if len(versions) > 1:
                dates = [v.get("published_at", 0) for v in versions.values() if isinstance(v, dict) and v.get("published_at")]
                if len(dates) >= 2:
                    features["update_frequency_days"] = (max(dates) - min(dates)) / (len(dates) - 1) / 86400
                else:
                    features["update_frequency_days"] = 365
            else:
                features["update_frequency_days"] = 365

            deps = metadata.get("dependencies", {})
            features["dependency_count"] = len(deps)
            features["dev_dependency_count"] = len(metadata.get("devDependencies", {}))

            # Padrões de nomeação
            features["typosquatting_score"] = self._calculate_typosquatting_score(package_name)
            features["name_entropy"] = self._calculate_entropy(package_name)
            features["contains_numbers"] = 1.0 if any(c.isdigit() for c in package_name) else 0.0

            # Histórico de segurança
            features["known_vulnerabilities"] = metadata.get("vulnerability_count", 0)
            features["maintainer_changes_count"] = metadata.get("maintainer_changes", 0)
            features["suspicious_version_jumps"] = self._detect_suspicious_jumps(versions)

            # Rede de dependências
            features["transitive_deps_count"] = self._count_transitive_deps(deps)
            features["high_risk_transitive_deps"] = self._count_high_risk_transitive(deps)
            features["circular_dependency_depth"] = self._detect_circular_deps(deps)

        # Comportamento do código (análise estática simulada)
        # Em produção: analisar tarball do pacote
        code_features = await self._analyze_code_behavior(package_name, version)
        features.update(code_features)

        # Preencher features faltantes com valores padrão
        for feat in self.BEHAVIORAL_FEATURES:
            if feat not in features:
                features[feat] = 0.0

        return features

    def _calculate_typosquatting_score(self, package_name: str) -> float:
        """Calcula score de typosquatting baseado em similaridade a pacotes populares."""
        # Mock: em produção, comparar com lista de pacotes populares via Levenshtein
        popular = ["react", "express", "lodash", "axios", "webpack", "babel", "typescript"]

        for pop in popular:
            if package_name.lower() != pop.lower():
                # Similaridade simples: prefixo/sufixo
                if package_name.startswith(pop) or package_name.endswith(pop):
                    return 0.8
                # Troca de caracteres adjacentes
                if len(package_name) == len(pop):
                    diffs = sum(a != b for a, b in zip(package_name, pop))
                    if diffs == 1:
                        return 0.9
        return 0.0

    def _calculate_entropy(self, text: str) -> float:
        """Calcula entropia de Shannon do texto."""
        from collections import Counter
        import math
        if not text:
            return 0.0
        counter = Counter(text.lower())
        length = len(text)
        return -sum((count/length) * math.log2(count/length) for count in counter.values())

    def _detect_suspicious_jumps(self, versions: Dict) -> float:
        """Detecta saltos de versão suspeitos."""
        if not versions:
            return 0.0
        # Mock: verificar se há saltos maiores que 2 versões major
        return 0.0  # Implementação completa requer parsing semver

    def _count_transitive_deps(self, deps: Dict) -> int:
        """Conta dependências transitivas (mock)."""
        return len(deps) * 3  # Estimativa simplificada

    def _count_high_risk_transitive(self, deps: Dict) -> int:
        """Conta dependências transitivas de alto risco (mock)."""
        return sum(1 for d in deps if isinstance(d, str) and "unsafe" in d.lower() or "deprecated" in (deps.get(d) if isinstance(deps.get(d), dict) else {}).get("description", "").lower())

    def _detect_circular_deps(self, deps: Dict) -> int:
        """Detecta profundidade de dependências circulares (mock)."""
        return 0  # Implementação completa requer análise de grafo

    async def _analyze_code_behavior(
        self,
        package_name: str,
        version: str
    ) -> Dict[str, float]:
        """Analisa comportamento do código do pacote (análise estática)."""
        # Mock: em produção, baixar tarball e analisar AST
        # Aqui, simulamos baseado em nome do pacote
        suspicious_names = ["malware", "stealer", "miner", "backdoor", "keylogger", "suspicious-pkg"]

        if any(s in package_name.lower() for s in suspicious_names):
            return {
                "uses_eval": 1.0,
                "uses_child_process": 1.0,
                "uses_network_calls": 1.0,
                "uses_file_system_write": 1.0,
                "obfuscation_score": 0.9
            }

        return {
            "uses_eval": 0.1,
            "uses_child_process": 0.0,
            "uses_network_calls": 0.2,
            "uses_file_system_write": 0.1,
            "obfuscation_score": 0.1
        }

    def _heuristic_risk_score(self, features: Dict) -> float:
        """Calcula score de risco heurístico se modelo não disponível."""
        score = 0.0

        # Penalizar pacotes muito novos
        if features.get("package_age_days", 365) < 30:
            score += 0.2

        # Penalizar typosquatting
        score += features.get("typosquatting_score", 0) * 0.3

        # Penalizar vulnerabilidades conhecidas
        score += min(0.3, features.get("known_vulnerabilities", 0) * 0.1)

        # Penalizar comportamento suspeito no código
        code_risk = (
            features.get("uses_eval", 0) * 0.1 +
            features.get("uses_child_process", 0) * 0.15 +
            features.get("obfuscation_score", 0) * 0.1 +
            features.get("uses_network_calls", 0) * 0.2 +
            features.get("uses_file_system_write", 0) * 0.2
        )
        score += code_risk

        return min(1.0, score)

    def _identify_risk_factors(
        self,
        features: Dict,
        risk_score: float
    ) -> Dict[str, float]:
        """Identifica fatores que mais contribuem para o risco."""
        factors = {}

        if features.get("typosquatting_score", 0) > 0.5:
            factors["typosquatting"] = features["typosquatting_score"] * 0.3

        if features.get("known_vulnerabilities", 0) > 0:
            factors["known_vulnerabilities"] = min(0.3, features["known_vulnerabilities"] * 0.1)

        if features.get("package_age_days", 365) < 30:
            factors["new_package"] = 0.2

        if features.get("uses_eval", 0) > 0.5 or features.get("obfuscation_score", 0) > 0.7:
            factors["suspicious_code"] = 0.25

        if features.get("high_risk_transitive_deps", 0) > 2:
            factors["risky_dependencies"] = 0.15

        # Normalizar para somar ~risk_score
        total = sum(factors.values())
        if total > 0:
            scale = risk_score / total
            factors = {k: v * scale for k, v in factors.items()}

        return factors if factors else {"baseline_risk": risk_score}

    def _generate_recommendations(
        self,
        risk_score: float,
        risk_factors: Dict
    ) -> List[str]:
        """Gera recomendações acionáveis baseadas no risco."""
        recommendations = []

        if risk_score >= self.RISK_THRESHOLDS["block_threshold"]:
            recommendations.append("🚫 BLOQUEAR: Pacote classificado como potencialmente malicioso")
            recommendations.append("• Revisar manualmente o código do pacote antes de qualquer exceção")
            recommendations.append("• Considerar alternativas mais estabelecidas")

        elif risk_score >= self.RISK_THRESHOLDS["high_risk"]:
            recommendations.append("⚠️  ALTO RISCO: Revisão manual obrigatória antes de usar em produção")
            if "typosquatting" in risk_factors:
                recommendations.append("• Verificar se o nome do pacote não é typosquatting de um pacote popular")
            if "known_vulnerabilities" in risk_factors:
                recommendations.append("• Corrigir vulnerabilidades conhecidas ou buscar versão patched")

        elif risk_score >= self.RISK_THRESHOLDS["medium_risk"]:
            recommendations.append("🟡 RISCO MÉDIO: Usar com cautela, monitorar atualizações")
            recommendations.append("• Pin versão exata no package.json para evitar atualizações automáticas")
            recommendations.append("• Configurar alertas para novas vulnerabilidades")

        else:
            recommendations.append("✅ BAIXO RISCO: Pacote parece seguro para uso")
            recommendations.append("• Manter dependências atualizadas via npm audit")

        return recommendations

    def _load_model(self):
        """Carrega modelo treinado do disco."""
        try:
            import joblib
            model_package = joblib.load(self.model_path / "malicious_dep_model.pkl")
            self._scaler = model_package["scaler"]
            self._isolation_forest = model_package["isolation_forest"]
            self._classifier = model_package["classifier"]
            logger.info(f"✅ Modelo carregado: {self.model_path / 'malicious_dep_model.pkl'}")
        except Exception as e:
            logger.warning(f"⚠️  Falha ao carregar modelo: {e}")

    async def train_model(
        self,
        training_data: pd.DataFrame,
        model_name: str = "malicious_dep_v1"
    ) -> Dict:
        """
        Treina modelo para detecção de dependências maliciosas.

        Args:
            training_data: DataFrame com features e label "is_malicious"
            model_name: Nome do modelo para exportação

        Returns:
            Dict com métricas de treinamento
        """
        logger.info(f"🧠 Iniciando treinamento do detector: {model_name}")

        # Preparar dados
        X = training_data[self.BEHAVIORAL_FEATURES].values
        y = training_data["is_malicious"].values

        if len(np.unique(y)) <= 1:
            # Not enough classes for stratify
            stratify = None
        else:
            stratify = y

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )

        # Treinar Isolation Forest
        self._isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,  # Esperamos ~5% de pacotes maliciosos
            random_state=42,
            n_jobs=-1
        )
        self._isolation_forest.fit(X_train)

        # Treinar Random Forest
        self._classifier = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        self._classifier.fit(X_train, y_train)

        # Avaliar
        from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
        y_pred = self._classifier.predict(X_test)

        # Handle the case where we only have one class during testing/training
        if self._classifier.classes_.shape[0] > 1:
            y_proba = self._classifier.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.0
        else:
            y_proba = np.zeros_like(y_pred)
            auc = 0.0

        metrics = {
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1_score": f1_score(y_test, y_pred, zero_division=0),
            "auc_roc": auc
        }

        # Exportar modelo
        import joblib
        model_package = {
            "model_name": model_name,
            "scaler": self._scaler,
            "isolation_forest": self._isolation_forest,
            "classifier": self._classifier,
            "feature_names": self.BEHAVIORAL_FEATURES,
            "metrics": metrics,
            "trained_at": time.time()
        }
        joblib.dump(model_package, self.model_path / f"{model_name}.pkl")

        logger.info(
            f"✅ Modelo treinado: {model_name} | "
            f"F1={metrics['f1_score']:.3f} | AUC={metrics['auc_roc']:.3f}"
        )

        return metrics

    def get_detector_statistics(self) -> Dict:
        """Retorna estatísticas do detector."""
        if not self._assessment_history:
            return {"total_assessments": 0}

        malicious_count = sum(1 for a in self._assessment_history if a.is_malicious)

        return {
            "total_assessments": len(self._assessment_history),
            "malicious_detected": malicious_count,
            "detection_rate": malicious_count / len(self._assessment_history),
            "avg_risk_score": sum(a.risk_score for a in self._assessment_history) / len(self._assessment_history),
            "model_loaded": self._classifier is not None,
            "popular_packages_cached": len(self._popular_packages)
        }
