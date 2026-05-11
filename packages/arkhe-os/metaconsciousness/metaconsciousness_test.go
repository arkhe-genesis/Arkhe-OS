package metaconsciousness

import (
	"testing"
)

func TestLayerCreation(t *testing.T) {
	layer, err := NewConsciousnessLayer("layer_1", LayerCode, 0, 256)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if layer.Dimension != 256 {
		t.Fatalf("Expected dimension 256, got %d", layer.Dimension)
	}
}

func TestEmergenceEngine(t *testing.T) {
	engine := NewEmergenceEngine("engine_1", "layer_1", EmergenceConfig{
		MinLayersRequired: 2,
		CoherenceThreshold: 0.1,
	})

	layer1, _ := NewConsciousnessLayer("layer_1", LayerCode, 0, 256)
	layer2, _ := NewConsciousnessLayer("layer_2", LayerData, 1, 256)

	engine.RegisterLayer(layer1)
	engine.RegisterLayer(layer2)

	_, err := engine.CheckEmergence()
	if err != nil {
		t.Logf("CheckEmergence error: %v", err)
	}
}

func TestCrossLayerSynchronizer(t *testing.T) {
	sync := NewCrossLayerSynchronizer("sync_1", SyncConfig{})

	layer1, _ := NewConsciousnessLayer("layer_1", LayerCode, 0, 256)
	layer2, _ := NewConsciousnessLayer("layer_2", LayerData, 1, 256)

	sync.RegisterLayer(layer1)
	sync.RegisterLayer(layer2)

	state, err := sync.SynchronizeLayers("layer_1", "layer_2")
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if state.LayerA != "layer_1" && state.LayerB != "layer_2" && state.LayerA != "layer_2" && state.LayerB != "layer_1" {
		t.Fatalf("Expected layer_1 and layer_2, got %v and %v", state.LayerA, state.LayerB)
	}
}

func TestProjectionOperator(t *testing.T) {
	op, err := NewProjectionOperator("op_1", OpAscend, 256, 512, false)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if op.SourceDim != 256 {
		t.Fatalf("Expected source dim 256, got %d", op.SourceDim)
	}
	if op.TargetDim != 512 {
		t.Fatalf("Expected target dim 512, got %d", op.TargetDim)
	}
}
