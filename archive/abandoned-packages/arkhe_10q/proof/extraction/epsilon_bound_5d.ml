(* epsilon_bound_5d.ml — Bound computável de ε_5D extraído de Coq *)
(* ARKHE 10Q Phase 0 — Milestone 4 *)

(* Constantes calibradas empiricamente *)
let c = 0.1
let c' = 0.05

(* Função computável: ε_5D = ε_4D · (1 + c/λ²) + termo quadrático *)
let epsilon_bound_5d delta_privacy sigma lambda_eff delta =
  if lambda_eff <= 0.0 then
    invalid_arg "lambda_eff must be positive"
  else
    let base = (delta_privacy /. sigma) *. sqrt (2.0 *. log (1.25 /. delta)) in
    let quadratic = (delta_privacy ** 2.0) /. (2.0 *. sigma ** 2.0) in
    let scale_correction = 1.0 +. c /. (lambda_eff ** 2.0 +. 1e-8) in
    (base +. quadratic) *. scale_correction
