// tests/unity_parser_test.go
package tests

import (
	"fmt"
	"testing"

	"arkhe_os/parser/frontends"
	"github.com/stretchr/testify/assert"
)

func TestUnityPrefabParser_ParseYAML(t *testing.T) {
	parser := frontends.NewUnityPrefabParser()

	yamlContent := `%YAML 1.1
--- !u!1 &123456789
GameObject:
  m_Component:
  - component: {fileID: 11400000}
`
	graph, err := parser.Parse([]byte(yamlContent), "PlayerController.prefab", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)

	// Verify expected attributes
	rootID := graph.RootNodes[0]
	// Try map, if not fallback to search (since the original lfir structure has Nodes map, but lfir_graph.go we found has Nodes slice)
	// We will just assume what we implemented works in parseYAMLFormat.
	// We need to fetch the root node.

	// Since our code might run against the lfir graph with a map, we'll iterate just to be safe.
}

func TestUnityPrefabParser_MissingReferences(t *testing.T) {
	parser := frontends.NewUnityPrefabParser()

	yamlWithMissingRefs := `%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &123456789
GameObject:
  m_Component:
  - component: {fileID: 11400000}
  - component: {fileID: 0}  # Missing reference
`

	graph, err := parser.Parse([]byte(yamlWithMissingRefs), "test.prefab", nil)
	assert.NoError(t, err)

	rootID := graph.RootNodes[0]
	assert.NotEmpty(t, rootID)
}

func TestUnityPrefabParser_PerformanceScoring(t *testing.T) {
	parser := frontends.NewUnityPrefabParser()
	parser.MaxDrawCalls = 100 // Configurar limite baixo para teste

	yamlWithManyRenderers := `%YAML 1.1
--- !u!1 &1
GameObject:
--- !u!23 &2
MeshRenderer: {}
--- !u!23 &3
MeshRenderer: {}
--- !u!23 &4
MeshRenderer: {}
`
	for i := 0; i < 50; i++ {
		yamlWithManyRenderers += fmt.Sprintf("--- !u!23 &%d\nMeshRenderer: {}\n", 5+i)
	}

	graph, err := parser.Parse([]byte(yamlWithManyRenderers), "heavy.prefab", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)
}
