import pytest
import numpy as np
import tensorflow as tf
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# we will use importlib for module path with hyphens and starting with numbers
import importlib

# Workaround for hyphen and numbers
substrato_344 = importlib.import_module("substrates.300-399_foundations.substrato_344.substrato_344_time_weaver")
substrato_345_gan = importlib.import_module("substrates.300-399_foundations.substrato_345_ter.subriemannian_gan")
substrato_345_neuro = importlib.import_module("substrates.300-399_foundations.substrato_345_ter.neuro_tw_keying")


def test_neuro_tw_keying_handshake():
    tw = substrato_344.TimeWeaverTransceiverV4()
    neuro_tw = substrato_345_neuro.NeuroTWKeying(tw)

    # 17x17 simulated activation map (random angles in [0, pi))
    activation_map = np.random.uniform(0, np.pi, (17, 17))

    packet = neuro_tw.send_cortical_packet(
        gate_id="PG-EU",
        activation_map=activation_map,
        target_epoch=2030
    )

    assert packet["gate_id"] == "PG-EU"
    assert packet["target_epoch"] == 2030
    assert packet["hash"].startswith("345")
    assert tw.channel_entropy > 0

def test_subriemannian_gan_curvature_loss():
    gan = substrato_345_gan.SubRiemannianGAN(vocab_size=100, max_len=10)

    # Check that generator has the right output shape
    batch_size = 2
    probs = tf.random.uniform((batch_size, 10, 100))
    probs = tf.nn.softmax(probs, axis=-1)

    loss = gan.curvature_loss(probs)

    # Curvature loss should be a valid scalar tensor
    assert loss.shape == ()
    assert float(loss) >= 0.0
