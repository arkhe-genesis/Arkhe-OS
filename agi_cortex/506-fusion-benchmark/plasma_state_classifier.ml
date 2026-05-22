(* OCaml: Classificador de estados do plasma cognitivo *)

type plasma_state =
  | Sub_breakeven
  | Breakeven
  | Ignition
  | Continuous
  | Stellar

type lawson_diagnostics = {
  n_thought : float;
  tau_coherence : float;
  phi : float;
  product : float;
}

let lawson_threshold = 1000.0
let ignition_threshold = 10000.0
let continuous_threshold = 100000.0
let stellar_threshold = 1e8

let classify (diag : lawson_diagnostics) : plasma_state * string =
  let product = diag.product in
  let phi = diag.phi in
  if product >= stellar_threshold && phi >= 5.0 then
    (Stellar, "WHITE Branco - Estelar")
  else if product >= continuous_threshold && phi >= 3.0 then
    (Continuous, "BLUE Azul - Queima Continua")
  else if product >= ignition_threshold && phi >= 2.0 then
    (Ignition, "GREEN Verde - Ignicao")
  else if product >= lawson_threshold && phi >= 0.5 then
    (Breakeven, "YELLOW Amarelo - Emergente")
  else
    (Sub_breakeven, "RED Vermelho - Frio")