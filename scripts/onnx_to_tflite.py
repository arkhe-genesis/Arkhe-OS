import onnx
import tensorflow as tf
from pathlib import Path

def convert_onnx_to_tflite(onnx_path: str, tflite_path: str):
    """Converte modelo ONNX para TensorFlow Lite (para microcontroladores)."""

    # Carregar modelo ONNX
    onnx_model = onnx.load(onnx_path)

    # Converter via onnx2tf (requer pacote onnx2tf)
    # Nota: onnx2tf é experimental; para produção, considere exportar diretamente de PyTorch
    try:
        import onnx2tf
        onnx2tf.convert(
            input_onnx_file_path=onnx_path,
            output_folder_path=Path(tflite_path).parent,
            output_integer_quantized_tflite=True,
            quant_type="int8",
            verbose=True
        )
        print(f"✅ Converted: {tflite_path}")
    except ImportError:
        print("⚠️  onnx2tf not installed. Install with: pip install onnx2tf")
        print("   Alternative: export directly from PyTorch with torch.quantization")

    return tflite_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", required=True)
    parser.add_argument("--tflite", required=True)
    args = parser.parse_args()

    convert_onnx_to_tflite(args.onnx, args.tflite)
