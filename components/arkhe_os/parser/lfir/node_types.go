// parser/lfir/node_types.go
// Tipos de nós LFIR específicos para projetos de jogos
package lfir

// Game-specific node types
const (
	// Unity types
	LFIRNodeTypeUnityGameObject  LFIRNodeType = "unity_gameobject"
	LFIRNodeTypeUnityComponent   LFIRNodeType = "unity_component"
	LFIRNodeTypeUnityPrefab      LFIRNodeType = "unity_prefab"
	LFIRNodeTypeUnityScene       LFIRNodeType = "unity_scene"
	LFIRNodeTypeUnityAssetBundle LFIRNodeType = "unity_assetbundle"

	// Steam types
	LFIRNodeTypeSteamDepot      LFIRNodeType = "steam_depot"
	LFIRNodeTypeSteamAchievement LFIRNodeType = "steam_achievement"
	LFIRNodeTypeSteamBranch     LFIRNodeType = "steam_branch"
	LFIRNodeTypeSteamManifest   LFIRNodeType = "steam_manifest"

	// Workshop types
	LFIRNodeTypeWorkshopItem  LFIRNodeType = "workshop_item"
	LFIRNodeTypeWorkshopCreator LFIRNodeType = "workshop_creator"

    // Other types
	LFIRNodeTypeCollection      LFIRNodeType = "collection"
	LFIRNodeTypeAlert           LFIRNodeType = "alert"
)

type LFIRMetricKey string

const (
	// Game-specific metrics
	LFIRMetricUnityDrawCalls      LFIRMetricKey = "unity_draw_calls"
	LFIRMetricUnityMissingRefs    LFIRMetricKey = "unity_missing_refs"
	LFIRMetricSteamDepotIntegrity LFIRMetricKey = "steam_depot_integrity"
	LFIRMetricWorkshopEngagement  LFIRMetricKey = "workshop_engagement"
)

// UnityComponentTypes defines known Unity component types
var UnityComponentTypes = map[string]bool{
	"Transform": true,
	"MeshRenderer": true,
	"SkinnedMeshRenderer": true,
	"SpriteRenderer": true,
	"BoxCollider": true,
	"SphereCollider": true,
	"MeshCollider": true,
	"Rigidbody": true,
	"Animator": true,
	"AudioSource": true,
	"Light": true,
	"Camera": true,
	"ParticleSystem": true,
	"Canvas": true,
	"TextMeshPro": true,
}

// SteamAchievement represents a Steam achievement
type SteamAchievement struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Icon        string `json:"icon"`
	IconGray    string `json:"icon_gray"`
	Hidden      bool   `json:"hidden"`
}

// UnitySceneMetrics holds coherence metrics for Unity scenes
type UnitySceneMetrics struct {
	TotalGameObjects   int     `json:"total_gameobjects"`
	ActiveGameObjects  int     `json:"active_gameobjects"`
	MissingReferences  int     `json:"missing_references"`
	EstimatedDrawCalls int     `json:"estimated_draw_calls"`
	UtilizationScore   float64 `json:"utilization_score"`
	IntegrityScore     float64 `json:"integrity_score"`
	PerformanceScore   float64 `json:"performance_score"`
}

// SteamBuildMetrics holds coherence metrics for Steam builds
type SteamBuildMetrics struct {
	AppID             string  `json:"app_id"`
	DepotCount        int     `json:"depot_count"`
	TotalSizeGB       float64 `json:"total_size_gb"`
	FileCount         int     `json:"file_count"`
	MissingFiles      int     `json:"missing_files"`
	ChecksumMismatches int    `json:"checksum_mismatches"`
	IntegrityScore    float64 `json:"integrity_score"`
	CompletenessScore float64 `json:"completeness_score"`
	ReliabilityScore  float64 `json:"reliability_score"`
}
