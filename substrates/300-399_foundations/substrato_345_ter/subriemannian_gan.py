import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
import hashlib

class SubRiemannianGAN:
    def __init__(self, vocab_size=10000, max_len=512):
        self.max_len = max_len
        self.vocab_size = vocab_size
        self.generator = self._build_generator()
        self.discriminator = self._build_discriminator()

    def _build_generator(self):
        # Gerador baseado em difusão hipoelíptica: camadas transpostas que
        # suavizam o campo de orientação.
        model = tf.keras.Sequential([
            layers.Dense(32 * 32 * 16, input_shape=(100,)),
            layers.Reshape((32, 32, 16)),
            layers.Conv2DTranspose(64, (5,5), strides=(2,2), padding='same'),
            layers.BatchNormalization(),
            layers.LeakyReLU(),
            layers.Conv2DTranspose(32, (5,5), strides=(2,1), padding='same'),
            layers.BatchNormalization(),
            layers.LeakyReLU(),
            layers.Conv2DTranspose(self.max_len, (3, self.vocab_size),
                                   strides=(1,1), padding='same', activation='softmax')
        ])
        return model

    def _build_discriminator(self):
        model = tf.keras.Sequential([
            layers.Conv2D(32, (3,3), strides=2, input_shape=(self.max_len, self.vocab_size, 1)),
            layers.LeakyReLU(),
            layers.Conv2D(64, (3,3), strides=2),
            layers.LeakyReLU(),
            layers.Flatten(),
            layers.Dense(1, activation='sigmoid')
        ])
        return model

    def curvature_loss(self, generated_probs):
        """
        Energia de curvatura da trajetória no fibrado SE(2).
        generated_probs: (batch, seq_len, vocab_size)
        """
        token_pos = tf.argmax(generated_probs, axis=-1)  # (batch, seq_len)
        theta = 2 * np.pi * tf.cast(token_pos, tf.float32) / tf.cast(self.vocab_size, tf.float32)
        dtheta = theta[:, 1:] - theta[:, :-1]
        d2theta = dtheta[:, 1:] - dtheta[:, :-1]
        curvature = tf.norm(d2theta, axis=1)
        return tf.reduce_mean(curvature)

    def generator_loss(self, fake_output, generated_probs):
        adv_loss = tf.reduce_mean(
            tf.keras.losses.binary_crossentropy(tf.ones_like(fake_output), fake_output))
        curv_loss = 0.1 * self.curvature_loss(generated_probs)
        return adv_loss + curv_loss
