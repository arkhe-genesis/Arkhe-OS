# Makefile para compilação da prova Coq

COQC = coqc
COQDEP = coqdep
OCAMLC = ocamlc
OCAMLOPT = ocamlopt

# Arquivos fonte
VFILES = riemannian_dp_5d.v
MLFILES = extraction/epsilon_bound_5d.ml

# Alvos
all: riemannian_dp_5d.vo extraction

riemannian_dp_5d.vo: $(VFILES)
	$(COQC) riemannian_dp_5d.v

extraction: riemannian_dp_5d.vo
	coqtop -l riemannian_dp_5d.v -R . RiemannianDP5D \
		-exec 'Extraction "extraction/epsilon_bound_5d.ml" epsilon_bound_5d_computable.'

clean:
	rm -f *.vo *.glob extraction/*.ml extraction/*.mli

test: riemannian_dp_5d.vo
	coqtop -l riemannian_dp_5d.v -R . RiemannianDP5D -e "Test."

.PHONY: all clean test extraction
