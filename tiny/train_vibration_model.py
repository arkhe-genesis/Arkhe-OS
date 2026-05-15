import tensorflow as tf
import numpy as np
import json
import os

# Gerar dados sintéticos: 64 amostras de FFT de vibração
np.random.seed(192)
def generate_sample(normal=True):
    base = np.sin(np.linspace(0, 20*np.pi, 64)) * 0.1
    if not normal:
        base += np.sin(np.linspace(0, 50*np.pi, 64)) * 0.5  # anomalia
    base += np.random.normal(0, 0.02, 64)
    return base.astype(np.float32)

X = np.array([generate_sample(True) for _ in range(100)] +
             [generate_sample(False) for _ in range(20)])
y = np.array([0]*100 + [1]*20)

model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(16, activation='relu', input_shape=(64,)),
    tf.keras.layers.Dense(8, activation='relu'),
    tf.keras.layers.Dense(2, activation='softmax')
])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X, y, epochs=5, validation_split=0.2, verbose=0)

# Salvar modelo completo
os.makedirs('tiny', exist_ok=True)
model.save('tiny/anomaly_model.h5')
print("✅ Modelo Keras treinado e salvo.")
