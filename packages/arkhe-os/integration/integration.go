package integration

import "time"

type IntegrationEvent struct {
	EventType string
	ClusterID string
	Data      map[string]interface{}
	Timestamp time.Time
}
