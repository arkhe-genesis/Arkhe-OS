package audit

import "time"

// LedgerConfig config for DistributedLedger
type LedgerConfig struct {
	EnableCoSNARK bool
}

// DistributedLedger a ledger
type DistributedLedger struct {
	ID string
}

// NewDistributedLedger creates a new ledger
func NewDistributedLedger(id string, config LedgerConfig) *DistributedLedger {
	return &DistributedLedger{ID: id}
}

// LedgerEntry entry
type LedgerEntry struct {
	EntryType string
	Data      map[string]interface{}
}

// AppendEntry appends entry
func (l *DistributedLedger) AppendEntry(entry LedgerEntry) {
}

// ExportSnapshot exports
func (l *DistributedLedger) ExportSnapshot(path string, timeRange [2]time.Time, withProof bool) error {
	return nil
}
