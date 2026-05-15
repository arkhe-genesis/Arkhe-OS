import os
import pytest
import numpy as np
import tensorflow as tf
from substrato_192_tinyml_edge.model_trainer import train_and_export_model
from substrato_192_tinyml_edge.convert_tflite_to_c import convert_to_c_array

@pytest.fixture(scope="session", autouse=True)
def setup_models():
    """Generates the TFLite model and C arrays before running tests."""
    # Build model and tflite
    train_and_export_model()

    # Build C arrays
    tflite_path = "substrato_192_tinyml_edge/anomaly_model.tflite"
    c_file_path = "substrato_192_tinyml_edge/anomaly_model.cc"
    convert_to_c_array(tflite_path, c_file_path)

def test_tflite_model_exists():
    assert os.path.exists("substrato_192_tinyml_edge/anomaly_model.tflite")

def test_c_header_exists():
    assert os.path.exists("substrato_192_tinyml_edge/anomaly_model.cc")
    assert os.path.exists("substrato_192_tinyml_edge/anomaly_model.h")

def test_tflite_model_inference():
    # Load the TFLite model and allocate tensors
    interpreter = tf.lite.Interpreter(model_path="substrato_192_tinyml_edge/anomaly_model.tflite")
    interpreter.allocate_tensors()

    # Get input and output tensors
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    assert input_details[0]['shape'][1] == 64
    assert output_details[0]['shape'][1] == 2

    # Test with normal data
    np.random.seed(42)
    test_normal = np.random.normal(loc=0.0, scale=1.0, size=(1, 64)).astype(np.float32)

    # Since it's quantized, we might need to quantize the input if details require it
    if input_details[0]['dtype'] == np.int8:
        scale, zero_point = input_details[0]['quantization']
        test_normal = np.round(test_normal / scale + zero_point).astype(np.int8)

    interpreter.set_tensor(input_details[0]['index'], test_normal)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])

    assert len(output_data[0]) == 2
