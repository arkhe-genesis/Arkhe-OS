import os
import tensorflow as tf
import numpy as np

def train_and_export_model():
    # Gerar dados sintéticos para o sensor de vibração do SCADA
    np.random.seed(42)
    # 1000 amostras, 64 features cada
    X_normal = np.random.normal(loc=0.0, scale=1.0, size=(800, 64))
    X_anomaly = np.random.normal(loc=2.0, scale=1.5, size=(200, 64))
    X = np.vstack((X_normal, X_anomaly))

    # 0 = Normal, 1 = Anomalia
    y = np.hstack((np.zeros(800), np.ones(200)))

    # Misturar os dados
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]

    # Modelo neural 2 camadas (64 -> 8 -> 2)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(64,)),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(2, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2)

    # Converter para TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT] # Quantização

    # Função representativa para quantização INT8 completa
    def representative_dataset():
        for i in range(100):
            yield [X[i].astype(np.float32).reshape(1, 64)]

    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8

    tflite_model = converter.convert()

    output_path = os.path.join(os.path.dirname(__file__), 'anomaly_model.tflite')
    with open(output_path, 'wb') as f:
        f.write(tflite_model)

    print(f"Modelo TFLite exportado com sucesso: {output_path}")

if __name__ == "__main__":
    train_and_export_model()
