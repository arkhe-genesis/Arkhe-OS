(* arkhe_os/release/octra_verifier_zarith.ml *)
(* Verificação de integridade de releases com aritmética de precisão arbitrária via Zarith *)

open Zarith

(* Tipo para componentes de release *)
type release_component = {
  name: string;
  hash: string;  (* SHA-256 hex *)
  weight: int;   (* Peso para combinação ponderada *)
}

(* Converter string hex para Z.t *)
let hex_to_z (hex: string) : Z.t =
  let rec aux i acc =
    if i >= String.length hex then acc
    else
      let c = Char.code hex.[i] in
      let digit =
        if c >= 48 && c <= 57 then c - 48  (* '0'-'9' *)
        else if c >= 97 && c <= 102 then c - 87  (* 'a'-'f' *)
        else if c >= 65 && c <= 70 then c - 55  (* 'A'-'F' *)
        else invalid_arg "Invalid hex character"
      in
      aux (i + 1) (Z.add (Z.mul acc (Z.of_int 16)) (Z.of_int digit))
  in
  aux 0 Z.zero

(* Converter Z.t para string hex *)
let z_to_hex (z: Z.t) : string =
  let rec aux z acc =
    if Z.equal z Z.zero then acc
    else
      let digit = Z.to_int (Z.rem z (Z.of_int 16)) in
      let char =
        if digit < 10 then Char.chr (digit + 48)
        else Char.chr (digit - 10 + 97)
      in
      aux (Z.div z (Z.of_int 16)) (String.make 1 char ^ acc)
  in
  if Z.equal z Z.zero then "0" else aux z ""

(* Primo grande para módulo de verificação *)
let verification_prime =
  Z.of_string "115792089237316195423570985008687907853269984665640564039457584007913129639937"

(* Calcular selo canônico a partir de componentes *)
let compute_canonical_seal (components: release_component list) : string =
  let weighted_sum =
    List.fold_left
      (fun acc comp ->
        let hash_z = hex_to_z comp.hash in
        let weight_z = Z.of_int comp.weight in
        Z.add acc (Z.mul hash_z weight_z)
      )
      Z.zero
      components
  in
  let seal = Z.rem weighted_sum verification_prime in
  z_to_hex seal

(* Verificar integridade de release *)
let verify_release_integrity
  (components: release_component list)
  (expected_seal: string)
  : bool =
  let computed_seal = compute_canonical_seal components in
  String.equal computed_seal expected_seal

(* Gerar prova de inclusão para componente em Merkle tree *)
let generate_merkle_proof
  (components: release_component list)
  (target_name: string)
  : string list =
  (* Implementação simplificada de prova de inclusão Merkle *)
  let hashes = List.map (fun c -> hex_to_z c.hash) components in
  (* Construir tree e gerar proof... *)
  []  (* Placeholder *)

(* Exportar para Python via js_of_ocaml ou ctypes *)
external verify_release_py : string -> string -> bool = "verify_release_integrity"
external compute_seal_py : string -> string = "compute_canonical_seal"
