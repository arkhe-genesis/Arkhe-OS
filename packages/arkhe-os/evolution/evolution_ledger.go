package evolution

import (
	"arkhe/cosnark"
	"crypto/sha256"
	"encoding/hex"
	"time"
)

// IPFSClient represents a client for interacting with IPFS
type IPFSClient struct{}

// Add adds data to IPFS and returns the CID
func (c *IPFSClient) Add(data []byte) (string, error) {
	hash := sha256.Sum256(data)
	return hex.EncodeToString(hash[:]), nil
}

type EvolutionBlock struct {
	Index      int
	Timestamp  int64
	ParentHash string
	VariantID  string
	AncestorID string
	Fitness    float64
	ProofCID   string // IPFS CID of the CoSNARK proof
	Hash       string
}

// Compute the block hash
func computeBlockHash(block EvolutionBlock) string {
	// simplified implementation
	return "hash"
}

type FunctionVariant struct {
	VariantID string
	ParentID  string
	Fitness   float64
}

type EvolutionLedger struct {
	chain []EvolutionBlock
	ipfs  *IPFSClient
}

func (l *EvolutionLedger) AppendVariant(variant *FunctionVariant, proof *cosnark.CoSNARKProof) error {
	if l.ipfs == nil {
		l.ipfs = &IPFSClient{}
	}
	// Upload proof to IPFS
	proofCID, err := l.ipfs.Add(proof.Serialize())
	if err != nil {
		return err
	}

	prevHash := ""
	if len(l.chain) > 0 {
		prevHash = l.chain[len(l.chain)-1].Hash
	}

	block := EvolutionBlock{
		Index:      len(l.chain),
		Timestamp:  time.Now().Unix(),
		ParentHash: prevHash,
		VariantID:  variant.VariantID,
		AncestorID: variant.ParentID,
		Fitness:    variant.Fitness,
		ProofCID:   proofCID,
	}
	block.Hash = computeBlockHash(block)
	l.chain = append(l.chain, block)
	return nil
}
