import binascii

def convert_to_c_array(tflite_path, c_file_path):
    with open(tflite_path, 'rb') as f:
        tflite_content = f.read()

    hex_data = binascii.hexlify(tflite_content).decode('utf-8')
    c_array = ", ".join([f"0x{hex_data[i:i+2]}" for i in range(0, len(hex_data), 2)])

    c_code = f"""// Generated from {tflite_path}
#include "anomaly_model.h"

// TFLite model data
const unsigned char anomaly_model_tflite[] = {{
    {c_array}
}};

// Length of the model data
const unsigned int anomaly_model_tflite_len = {len(tflite_content)};
"""

    with open(c_file_path, 'w') as f:
        f.write(c_code)

    h_code = f"""#ifndef ANOMALY_MODEL_H
#define ANOMALY_MODEL_H

extern const unsigned char anomaly_model_tflite[];
extern const unsigned int anomaly_model_tflite_len;

#endif // ANOMALY_MODEL_H
"""
    with open(c_file_path.replace('.cc', '.h').replace('.c', '.h'), 'w') as f:
        f.write(h_code)

if __name__ == "__main__":
    import os
    tflite_path = os.path.join(os.path.dirname(__file__), "anomaly_model.tflite")
    c_file_path = os.path.join(os.path.dirname(__file__), "anomaly_model.cc")
    convert_to_c_array(tflite_path, c_file_path)
    print("Convertido para C com sucesso!")
