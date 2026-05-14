#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bci_neural_interface.py — Substrato 7.4.0: Interface Neural para Visualização Quântica
Decodificação de sinais EEG/fNIRS para controle por pensamento de visualizações AR/VR.
"""

import numpy as np
import asyncio, json, time, hashlib
from typing import Optional, Dict, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

class NeuralSignalType(Enum):
    """Tipos de sinais neurais suportados."""
    EEG = auto()      # Eletroencefalografia: alta resolução temporal
    FNIRS = auto()    # Espectroscopia funcional no infravermelho próximo: resolução espacial
    COMBINED = auto() # Fusão EEG+fNIRS para melhor desempenho

@dataclass
class NeuralCommand:
    """Comando decodificado de sinal neural."""
    command_type: str  # "select_state", "rotate_view", "zoom", "filter_by_phi_c", etc.
    parameters: Dict
    confidence: float  # Confiança na decodificação (0-1)
    timestamp: float
    raw_signal_hash: str  # Hash do sinal bruto para auditoria

@dataclass
class BCIConfig:
    """Configuração da interface BCI."""
    signal_type: NeuralSignalType = NeuralSignalType.COMBINED
    sampling_rate_hz: int = 250  # Para EEG
    feature_extraction: str = "csp"  # Common Spatial Patterns para EEG
    classifier_model: str = "lda"  # Linear Discriminant Analysis
    calibration_required: bool = True
    phi_c_feedback: bool = True  # Feedback visual baseado em coerência Φ_C

class NeuralStateDecoder:
    """
    Decodificador de estados neurais para comandos de visualização quântica.

    Arquitetura:
    • Pré-processamento de sinais EEG/fNIRS (filtragem, artefato removal)
    • Extração de features: CSP para EEG, HbO/HbR para fNIRS
    • Classificação em tempo real com LDA/SVM/Redes Neurais
    • Mapeamento de intenções para comandos de visualização 3D
    • Feedback adaptativo baseado em coerência Φ_C do usuário
    """

    # Mapeamento de padrões neurais para comandos
    NEURAL_COMMAND_MAP = {
        "motor_imagery_left": {"command": "rotate_view", "params": {"axis": "y", "direction": -1}},
        "motor_imagery_right": {"command": "rotate_view", "params": {"axis": "y", "direction": 1}},
        "motor_imagery_up": {"command": "zoom", "params": {"factor": 1.2}},
        "motor_imagery_down": {"command": "zoom", "params": {"factor": 0.8}},
        "focus_high": {"command": "filter_by_phi_c", "params": {"min_phi_c": 0.99}},
        "focus_low": {"command": "filter_by_phi_c", "params": {"min_phi_c": 0.95}},
        "blink_double": {"command": "select_state", "params": {"mode": "nearest"}},
    }

    def __init__(self, config: BCIConfig):
        self.config = config
        self._calibrated = not config.calibration_required
        self._feature_extractor = None
        self._classifier = None
        self._phi_c_feedback_enabled = config.phi_c_feedback

        # Buffer de sinais para processamento em tempo real
        self.signal_buffer: List[np.ndarray] = []
        self.max_buffer_size = config.sampling_rate_hz * 2  # 2 segundos de buffer

    async def calibrate(self, user_id: str, training_data: List[Tuple[np.ndarray, str]]) -> bool:
        """Calibra decodificador com dados de treinamento do usuário."""
        if not training_data:
            return False

        # Extrair features dos sinais de treinamento
        X_train = []
        y_train = []

        for signal, label in training_data:
            features = self._extract_features(signal)
            if features is not None:
                X_train.append(features)
                y_train.append(label)

        if len(X_train) < 10:
            return False  # Dados insuficientes

        # Treinar extrator de features (CSP para EEG)
        if self.config.signal_type in [NeuralSignalType.EEG, NeuralSignalType.COMBINED]:
            self._feature_extractor = self._train_csp(np.array(X_train), y_train)

        # Treinar classificador
        self._classifier = self._train_classifier(np.array(X_train), y_train)

        self._calibrated = True
        return True

    def _extract_features(self, signal: np.ndarray) -> Optional[np.ndarray]:
        """Extrai features de sinal neural para classificação."""
        if signal.shape[-1] < 10:  # Sinal muito curto
            return None

        if self.config.signal_type in [NeuralSignalType.EEG, NeuralSignalType.COMBINED]:
            # Extrair bandas de frequência para EEG
            bands = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 13), "beta": (13, 30), "gamma": (30, 50)}
            features = []

            for band_name, (low, high) in bands.items():
                # Filtrar banda (simulado)
                band_power = np.mean(np.abs(signal) ** 2)  # Potência da banda
                features.append(band_power)

            return np.array(features)

        elif self.config.signal_type == NeuralSignalType.FNIRS:
            # Extrair HbO/HbR para fNIRS
            hbo = np.mean(signal[:, 0]) if signal.shape[1] > 0 else 0
            hbr = np.mean(signal[:, 1]) if signal.shape[1] > 1 else 0
            return np.array([hbo, hbr, hbo - hbr])  # Diferença como feature

        return None

    def _train_csp(self, X: np.ndarray, y: List[str]) -> any:
        """Treina Common Spatial Patterns para EEG."""
        # Implementação simplificada de CSP
        # Em produção: usar pyRiemann ou MNE-Python
        return {"trained": True, "n_components": 4}

    def _train_classifier(self, X: np.ndarray, y: List[str]) -> any:
        """Treina classificador para comandos neurais."""
        # Implementação simplificada de LDA
        # Em produção: usar scikit-learn com validação cruzada
        return {"trained": True, "classes": list(set(y))}

    async def decode_command(self, neural_signal: np.ndarray, user_phi_c: Optional[float] = None) -> Optional[NeuralCommand]:
        """Decodifica comando a partir de sinal neural em tempo real."""
        if not self._calibrated:
            return None

        # Adicionar ao buffer
        self.signal_buffer.append(neural_signal)
        if len(self.signal_buffer) > self.max_buffer_size:
            self.signal_buffer.pop(0)

        # Extrair features do buffer
        avg_signal = np.mean(self.signal_buffer[-10:], axis=0)  # Média dos últimos 10 samples
        features = self._extract_features(avg_signal)

        if features is None or self._classifier is None:
            return None

        # Classificar intenção
        predicted_class = self._classify(features)
        confidence = self._estimate_confidence(features, predicted_class)

        if confidence < 0.7:  # Threshold mínimo de confiança
            return None

        # Mapear para comando
        command_template = self.NEURAL_COMMAND_MAP.get(predicted_class)
        if not command_template:
            return None

        # Aplicar feedback baseado em Φ_C do usuário se habilitado
        params = command_template["params"].copy()
        if self._phi_c_feedback_enabled and user_phi_c is not None:
            params = self._apply_phi_c_feedback(params, user_phi_c)

        return NeuralCommand(
            command_type=command_template["command"],
            parameters=params,
            confidence=confidence,
            timestamp=time.time(),
            raw_signal_hash=hashlib.sha3_256(neural_signal.tobytes()).hexdigest()[:16],
        )

    def _classify(self, features: np.ndarray) -> str:
        """Classifica features em comando neural."""
        # Simulação: classificação baseada em padrões de features
        if features[0] > 0.8:  # Alta potência em banda delta
            return "focus_high"
        elif features[1] > 0.6:  # Alta potência em banda theta
            return "motor_imagery_left"
        elif features[2] > 0.7:  # Alta potência em banda alpha
            return "motor_imagery_right"
        elif features[3] > 0.5:  # Alta potência em banda beta
            return "blink_double"
        else:
            return "focus_low"

    def _estimate_confidence(self, features: np.ndarray, predicted_class: str) -> float:
        """Estima confiança na classificação."""
        # Heurística: confiança baseada na magnitude das features
        feature_magnitude = np.linalg.norm(features)
        base_confidence = min(1.0, feature_magnitude / 2.0)

        # Ajustar baseado na consistência com histórico recente
        recent_classes = [self._classify(self._extract_features(np.mean(buf[-5:], axis=0)))
                         for buf in [self.signal_buffer[-20:]] if len(self.signal_buffer) >= 5]
        if recent_classes and recent_classes[-1] == predicted_class:
            base_confidence = min(1.0, base_confidence + 0.1)

        return base_confidence

    def _apply_phi_c_feedback(self, params: Dict, user_phi_c: float) -> Dict:
        """Aplica feedback adaptativo baseado na coerência Φ_C do usuário."""
        # Se usuário tem alta coerência, permitir comandos mais precisos
        if user_phi_c > 0.99:
            if "factor" in params:
                params["factor"] = 1.0 + (params["factor"] - 1.0) * 1.5  # Zoom mais sensível
        elif user_phi_c < 0.95:
            # Se baixa coerência, suavizar comandos para evitar erros
            if "factor" in params:
                params["factor"] = 1.0 + (params["factor"] - 1.0) * 0.5  # Zoom menos sensível

        return params

class QuantumThoughtVisualizer:
    """
    Visualizador AR/VR controlado por interface neural.

    Integra NeuralStateDecoder com ARKHE IMMERSIVE para:
    • Seleção de estados quânticos por pensamento
    • Navegação 3D via imaginação motora
    • Filtragem por coerência Φ_C via foco cognitivo
    • Feedback visual adaptativo baseado em estado neural
    """

    def __init__(self, bci_config: BCIConfig, immersive_session):
        self.decoder = NeuralStateDecoder(bci_config)
        self.immersive = immersive_session  # Sessão AR/VR do ARKHE IMMERSIVE
        self.active_filters: Dict[str, any] = {}

    async def start_neural_control(self, neural_stream: asyncio.Queue, user_phi_c_provider: Callable[[], float]):
        """Inicia loop de controle neural para visualização quântica."""
        print("🧠 Iniciando controle neural para visualização quântica...")

        while True:
            try:
                # Obter sinal neural do stream
                neural_signal = await neural_stream.get()

                # Obter Φ_C atual do usuário (se disponível)
                user_phi_c = user_phi_c_provider() if user_phi_c_provider else None

                # Decodificar comando
                command = await self.decoder.decode_command(neural_signal, user_phi_c)

                if command:
                    # Executar comando na sessão imersiva
                    await self._execute_command(command)

                    # Feedback visual baseado na confiança
                    if command.confidence > 0.9:
                        await self.immersive.show_feedback("✓ Comando confirmado", color="green")
                    elif command.confidence < 0.75:
                        await self.immersive.show_feedback("⚠ Confiança baixa", color="yellow")

                # Aguardar próximo sinal
                await asyncio.sleep(0.01)  # 100Hz update rate

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Erro no loop neural: {e}")
                await asyncio.sleep(0.1)

    async def _execute_command(self, command: NeuralCommand):
        """Executa comando decodificado na sessão imersiva."""
        if command.command_type == "rotate_view":
            await self.immersive.rotate_view(
                axis=command.parameters["axis"],
                direction=command.parameters["direction"],
                speed=command.confidence,  # Velocidade proporcional à confiança
            )

        elif command.command_type == "zoom":
            await self.immersive.zoom(
                factor=command.parameters["factor"],
                smooth=command.confidence > 0.8,
            )

        elif command.command_type == "filter_by_phi_c":
            min_phi = command.parameters["min_phi_c"]
            await self.immersive.apply_filter(
                filter_type="phi_c_threshold",
                min_value=min_phi,
                highlight_high_coherence=True,
            )
            self.active_filters["phi_c"] = min_phi

        elif command.command_type == "select_state":
            mode = command.parameters.get("mode", "nearest")
            selected = await self.immersive.select_nearest_state(mode=mode)
            if selected:
                await self.immersive.show_state_details(selected)

# ============================================================================
# Exemplo: Visualização quântica controlada por pensamento
# ============================================================================
async def demo_bci_quantum_visualization():
    """Demonstra visualização quântica via interface neural."""

    # Configurar BCI
    bci_config = BCIConfig(
        signal_type=NeuralSignalType.COMBINED,
        calibration_required=False,  # Pular calibração para demo
        phi_c_feedback=True,
    )

    # Mock de sessão imersiva
    class MockImmersive:
        async def rotate_view(self, axis, direction, speed): print(f"🔄 Rotacionando {axis} {direction}x ({speed:.2f})")
        async def zoom(self, factor, smooth): print(f"🔍 Zoom {factor}x (smooth={smooth})")
        async def apply_filter(self, filter_type, min_value, **kwargs): print(f"🔎 Filtro {filter_type}: min Φ_C={min_value}")
        async def select_nearest_state(self, mode): print(f"🎯 Selecionando estado ({mode})"); return "state_123"
        async def show_state_details(self, state_id): print(f"📋 Detalhes de {state_id}")
        async def show_feedback(self, msg, color): print(f"💬 {msg}")

    visualizer = QuantumThoughtVisualizer(bci_config, MockImmersive())

    # Simular stream de sinais neurais
    async def neural_signal_generator():
        queue = asyncio.Queue()
        async def generate():
            for i in range(20):
                # Gerar sinal neural simulado
                signal = np.random.randn(32, 250) * 0.1  # 32 canais EEG, 250 samples
                # Adicionar padrão para comando específico
                if i % 5 == 0:
                    signal[0, :50] += 2.0  # Simular padrão "motor_imagery_left"
                await queue.put(signal)
                await asyncio.sleep(0.1)
        asyncio.create_task(generate())
        return queue

    neural_stream = await neural_signal_generator()

    # Provider simulado de Φ_C do usuário
    def get_user_phi_c():
        return 0.99 + np.random.random() * 0.01

    # Iniciar controle neural
    control_task = asyncio.create_task(
        visualizer.start_neural_control(neural_stream, get_user_phi_c)
    )

    # Executar por alguns segundos
    await asyncio.sleep(3)
    control_task.cancel()

    print("✅ Demo de controle neural concluída")

if __name__ == "__main__":
    asyncio.run(demo_bci_quantum_visualization())
