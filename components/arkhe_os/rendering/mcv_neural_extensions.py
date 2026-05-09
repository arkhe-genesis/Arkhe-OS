import torch
from arkhe_os.rendering.coherence_monitor import CoherenceRenderer
from arkhe_os.ai.coherence_cnn_classifier import CoherenceCNNClassifier
from arkhe_os.generative.conditional_coherence_generator import ConditionalCoherenceGenerator
from arkhe_os.neural.bci_neural_interface import BCINeuralInterface, NeuralModality, BCIProtocol

class EnhancedCoherenceMonitor:
    def __init__(self, resolution=(512, 512), device='cpu', enable_classification=True, enable_generation=True, enable_bci=True, bci_protocol='simulator'):
        self.renderer = CoherenceRenderer(resolution=resolution, device=device)
        self.enable_classification = enable_classification
        self.enable_generation = enable_generation
        self.enable_bci = enable_bci

        if enable_classification: self.classifier = CoherenceCNNClassifier().to(device)
        if enable_generation: self.generator = ConditionalCoherenceGenerator(device=device)
        if enable_bci: self.bci_interface = BCINeuralInterface(protocol=BCIProtocol.SIMULATOR, modality=NeuralModality.VISUAL)

        self.device = device
        self.last_classification = None

    def analyze_and_perceive(self, time, phi_c_value, spatial_metrics=None, condition=None, perceive_via_bci=True):
        result = {'timestamp': time, 'phi_c_input': phi_c_value}
        frame = self.renderer.render(time)
        result['frame_rendered'] = True

        if self.enable_classification:
            self.last_classification = self.classifier.classify(frame)
            result['classification'] = {'state': self.last_classification.state.name, 'confidence': self.last_classification.confidence}

        metrics = spatial_metrics or {}
        metrics['phi_c_visual'] = phi_c_value

        if self.enable_generation and condition:
            future_frame, shader_params = self.generator.generate_coherence_state(condition, n_variations=1, return_params=True)
            result['future_state_generated'] = True

        if self.enable_bci and perceive_via_bci:
            if not self.bci_interface.connected: self.bci_interface.connect()
            result['bci_perception'] = self.bci_interface.perceive_coherence(phi_c_value, metrics, condition, True)

        return result
