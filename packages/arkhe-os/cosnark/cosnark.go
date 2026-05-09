package cosnark

import "time"

type ZKStatement struct {
	FieldCommitment []byte
	ProofType       string
}

type CoSNARKProof struct {
	ProofID    string
	ProofBytes []byte
	Statement  ZKStatement
	Timestamp  time.Time
	NodeID     string
}

func (p *CoSNARKProof) Serialize() []byte {
	return p.ProofBytes
}
