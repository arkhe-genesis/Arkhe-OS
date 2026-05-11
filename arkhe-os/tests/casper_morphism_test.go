package tests

import (
	"testing"
	"arkhe-os/bridges/casper"
)

func TestMapChainToCasper(t *testing.T) {
	blocks := []casper.ArkheBlock{
		{Index: 0, Timestamp: 100.0, Hash: "hash0"},
		{Index: 1, Timestamp: 110.0, Hash: "hash1"},
		{Index: 2, Timestamp: 120.0, Hash: "hash2"},
	}

	epochs, err := casper.MapChainToCasper(blocks, 10)
	if err != nil {
		t.Fatalf("Esperado sucesso, obteve erro: %v", err)
	}

	if len(epochs) != len(blocks) {
		t.Fatalf("Comprimento incorreto. Esperado %d, obteve %d", len(blocks), len(epochs))
	}

	if epochs[0].EpochNumber != 10 || epochs[1].EpochNumber != 11 || epochs[2].EpochNumber != 12 {
		t.Errorf("Mapeamento de épocas incorreto")
	}
}

func TestMapChainToCasperInvalidOrder(t *testing.T) {
	blocks := []casper.ArkheBlock{
		{Index: 0, Timestamp: 100.0, Hash: "hash0"},
		{Index: 1, Timestamp: 90.0, Hash: "hash1"}, // Ordem inválida
	}

	_, err := casper.MapChainToCasper(blocks, 10)
	if err == nil {
		t.Fatalf("Esperado erro devido a ordem temporal inválida, obteve sucesso")
	}
}
