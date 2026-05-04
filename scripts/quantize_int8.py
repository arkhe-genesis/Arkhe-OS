import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType
from pathlib import Path

def quantize_arkhe_model(
    input_path: str,
    output_path: str,
    per_channel: bool = False,
    reduce_range: bool = False
):
    """
    Quantiza modelo ONNX do ARKHE para INT8.

    Ideal para microcontroladores (ESP32, Raspberry Pi Pico, etc.)
    """
    print(f"🔧 Quantizing {input_path} → {output_path}")

    # Verificar se o modelo existe
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Model not found: {input_path}")

    # Quantização dinâmica (pesos → INT8, ativações → float32)
    # Mais estável para modelos com ativações esparsas como SAE
    quantize_dynamic(
        model_input=input_path,
        model_output=output_path,
        weight_type=QuantType.QInt8,  # INT8 para pesos
        per_channel=per_channel,
        reduce_range=reduce_range,
        # Otimizações para edge
        optimize_model=True,
        use_external_data_format=False  # Único arquivo para microcontroladores
    )

    # Verificar tamanho
    original_size = Path(input_path).stat().st_size / 1024
    quantized_size = Path(output_path).stat().st_size / 1024
    reduction = (1 - quantized_size / original_size) * 100

    print(f"✅ Quantization complete:")
    print(f"   • Original: {original_size:.1f} KB")
    print(f"   • Quantized: {quantized_size:.1f} KB")
    print(f"   • Reduction: {reduction:.1f}%")

    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Caminho do modelo ONNX")
    parser.add_argument("--output", required=True, help="Caminho de saída")
    parser.add_argument("--per-channel", action="store_true", help="Quantização por canal")
    args = parser.parse_args()

    quantize_arkhe_model(args.input, args.output, args.per_channel)
