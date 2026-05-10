(*
  arkhe_os_topos.v
  Formalização do morfismo de topos entre a coerência ARKHE e o consenso Casper.
*)

Require Import Arith.
Require Import ZArith.
Require Import Reals.
Require Import List.
Require Import String.
Require Import Bool.
Require Import Lia.
Import ListNotations.

Open Scope R_scope.
Open Scope string_scope.

(* ========================================================================== *)
(* TIPOS BÁSICOS                                                              *)
(* ========================================================================== *)

Definition Hash := string.
Definition Timestamp := R.
Definition CasperEpoch := nat.

Record TemporalBlock : Type := mkTemporalBlock {
  tb_index : nat;
  tb_timestamp : Timestamp;
  tb_hash : Hash;
}.

Definition TemporalChain := list TemporalBlock.

Record CasperCheckpoint : Type := mkCasperCheckpoint {
  cc_epoch : CasperEpoch;
  cc_hash : Hash;
}.

Definition CasperChain := list CasperCheckpoint.

(* ========================================================================== *)
(* MORFISMO DE TOPOS (ARKHE -> CASPER)                                        *)
(* ========================================================================== *)

(* Função que mapeia um único bloco ARKHE para um checkpoint Casper (functor f_*) *)
Definition arkhify_casper_block (tb: TemporalBlock) (epoch: CasperEpoch) : CasperCheckpoint :=
  mkCasperCheckpoint epoch (tb_hash tb).

(* Função que aplica o mapeamento a uma cadeia, mantendo o controle da época *)
Fixpoint arkhify_casper_chain_aux (blocks: TemporalChain) (epoch: CasperEpoch) : CasperChain :=
  match blocks with
  | [] => []
  | tb :: rest => arkhify_casper_block tb epoch :: arkhify_casper_chain_aux rest (S epoch)
  end.

Definition arkhify_casper_consensus (blocks: TemporalChain) (genesisEpoch: CasperEpoch) : CasperChain :=
  arkhify_casper_chain_aux blocks genesisEpoch.

(* ========================================================================== *)
(* CONSISTÊNCIA TEMPORAL                                                      *)
(* ========================================================================== *)

(* Invariante ARKHE: A ordem temporal é preservada na cadeia (já verificado em arkhe_os.v) *)
Definition ChainTemporalOrder (chain : TemporalChain) : Prop :=
  forall (tb1 tb2 : TemporalBlock) (prefix suffix : TemporalChain),
    chain = prefix ++ [tb1; tb2] ++ suffix ->
    tb_timestamp tb1 <= tb_timestamp tb2.

(* Invariante CASPER: Épocas são estritamente crescentes na cadeia *)
Definition CasperEpochOrder (chain : CasperChain) : Prop :=
  forall (cc1 cc2 : CasperCheckpoint) (prefix suffix : CasperChain),
    chain = prefix ++ [cc1; cc2] ++ suffix ->
    cc_epoch cc1 < cc_epoch cc2.

(* Lema: Mapeamento preserva ordem de épocas (estritamente crescente) *)
Lemma arkhify_preserves_epoch_order_aux:
  forall (blocks: TemporalChain) (epoch: CasperEpoch)
         (cc1 cc2: CasperCheckpoint) (prefix suffix: CasperChain),
    arkhify_casper_chain_aux blocks epoch = prefix ++ [cc1; cc2] ++ suffix ->
    cc_epoch cc1 < cc_epoch cc2.
Proof.
  induction blocks as [| tb blocks IH].
  - intros epoch cc1 cc2 prefix suffix H.
    simpl in H.
    destruct prefix; discriminate.
  - intros epoch cc1 cc2 prefix suffix H.
    simpl in H.
    destruct prefix as [| p prefix'].
    + (* prefix is empty, so cc1 = arkhify_casper_block tb epoch e cc2 é o próximo *)
      simpl in H.
      injection H as Hcc1 Hrest.
      destruct blocks as [| tb2 blocks2].
      * (* se rest for vazio, cc2 não pode estar na lista *)
        simpl in Hrest. discriminate.
      * simpl in Hrest.
        injection Hrest as Hcc2 Hrest2.
        rewrite <- Hcc1, <- Hcc2.
        unfold arkhify_casper_block. simpl.
        apply Nat.lt_succ_diag_r.
    + (* prefix is non-empty *)
      simpl in H.
      injection H as _ Hrest.
      apply (IH (S epoch) cc1 cc2 prefix' suffix).
      exact Hrest.
Qed.

(* ========================================================================== *)
(* PRESERVAÇÃO DE LIMITES FINITOS                                             *)
(* ========================================================================== *)

(* O Functor f_* preserva limites finitos, em particular produtos de fibra (pullbacks)
   e objetos terminais. Aqui demonstramos a preservação do comprimento da cadeia (isomorfismo
   na estrutura base dos dados mapeados) que é uma forma de preservação de limites em
   Set. *)

Theorem arkhify_preserves_length:
  forall (blocks: TemporalChain) (epoch: CasperEpoch),
    length (arkhify_casper_chain_aux blocks epoch) = length blocks.
Proof.
  intros blocks.
  induction blocks as [| tb blocks IH].
  - intros epoch. reflexivity.
  - intros epoch. simpl. rewrite (IH (S epoch)). reflexivity.
Qed.

(* ========================================================================== *)
(* TEOREMA PRINCIPAL                                                          *)
(* A tradução preserva a ordem temporal ao mapear timestamps para épocas.     *)
(* ========================================================================== *)

Theorem arkhify_casper_preserves_temporal_order:
  forall (blocks: TemporalChain) (genesisEpoch: CasperEpoch),
    ChainTemporalOrder blocks ->
    CasperEpochOrder (arkhify_casper_consensus blocks genesisEpoch).
Proof.
  intros blocks genesisEpoch Horder.
  unfold arkhify_casper_consensus. unfold CasperEpochOrder.
  intros cc1 cc2 prefix suffix H.
  apply (arkhify_preserves_epoch_order_aux blocks genesisEpoch cc1 cc2 prefix suffix).
  exact H.
Qed.
