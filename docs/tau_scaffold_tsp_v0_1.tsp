// TypeSpec IR — Definição formal do token que flui VRP → DDR → RHO
@doc("Token de Região de Interesse gerado pelo VRP v1.1")
model ROIToken {
  @doc("Coordenadas espaciais do voxel (mm)")
  x: int16;
  y: int16;
  z: int16;

  @doc("Flags de classificação cromática")
  flags: {
    is_red_dominant: boolean;
    is_green_dominant: boolean;
    is_blue_dominant: boolean;
    is_high_intensity: boolean;
  };

  @doc("Intensidade do sinal (MSB do campo original)")
  intensity_msb: uint8;

  @doc("Timestamp do frame (injetado pelo NOC bridge)")
  frame_timestamp: uint64;

  @doc("ID do stream (para múltiplos Lidars)")
  stream_id: uint8;
}
