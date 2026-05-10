package casper

import (
	"errors"
)

type ArkheBlock struct {
	Index     int
	Timestamp float64
	Hash      string
}

type Epoch struct {
	EpochNumber uint64
	Hash        string
}

// MapBlockToEpoch mapeia um bloco ARKHE para uma época Casper
func MapBlockToEpoch(block ArkheBlock, genesisEpoch uint64) Epoch {
	return Epoch{
		EpochNumber: genesisEpoch + uint64(block.Index),
		Hash:        block.Hash,
	}
}

// VerifyTemporalConsistency verifica se a ordem temporal é preservada na cadeia
func VerifyTemporalConsistency(blocks []ArkheBlock) error {
	if len(blocks) < 2 {
		return nil
	}

	for i := 1; i < len(blocks); i++ {
		if blocks[i].Timestamp < blocks[i-1].Timestamp {
			return errors.New("ordem temporal não preservada: timestamp decrescente")
		}
	}
	return nil
}

// MapChainToCasper mapeia uma cadeia de blocos ARKHE para checkpoints Casper, garantindo consistência
func MapChainToCasper(blocks []ArkheBlock, genesisEpoch uint64) ([]Epoch, error) {
	if err := VerifyTemporalConsistency(blocks); err != nil {
		return nil, err
	}

	epochs := make([]Epoch, len(blocks))
	for i, block := range blocks {
		epochs[i] = MapBlockToEpoch(block, genesisEpoch)
	}

	return epochs, nil
}
