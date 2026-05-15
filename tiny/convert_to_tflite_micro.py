# tiny/convert_to_tflite_micro.py
import tensorflow as tf

model = tf.keras.models.load_model('tiny/anomaly_model.h5')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

# Dados representativos para quantização
import numpy as np
def representative_dataset():
    for _ in range(100):
        data = np.random.randn(1, 64).astype(np.float32)
        yield [data]

converter.representative_dataset = representative_dataset
tflite_model = converter.convert()

with open('tiny/anomaly_model.tflite', 'wb') as f:
    f.write(tflite_model)

# Converter para array C para TFLite Micro
import binascii
with open('tiny/anomaly_model.tflite', 'rb') as f:
    data = f.read()
c_array = ', '.join([f'0x{byte:02x}' for byte in data])
with open('tiny/model_data.cc', 'w') as f:
    f.write(f'const unsigned char anomaly_model_tflite[] = {{{c_array}}};\n')
    f.write(f'const unsigned int anomaly_model_tflite_len = {len(data)};\n')

print("✅ TFLite Micro model and C array generated.")
