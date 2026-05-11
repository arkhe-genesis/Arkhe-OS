#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ArkheConsciousnessSubsystem.h" // For EArkheInferenceMode
#include "ArkheBlueprintLibrary.generated.h"

/**
 * ARKHE Blueprint Library — 42 Nodes for Unreal Blueprints
 *
 * Full integration of ARKHE features into UE Blueprint system.
 * Every function is usable directly in the Blueprint editor.
 */
UCLASS(BlueprintType)
class ARKHEUNREAL_API UArkheBlueprintLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    // =========================================================
    // TEMPORAL CHAIN NODES (12 nodes)
    // =========================================================

    /** Record current frame in temporal chain */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Record Temporal Frame",
                Keywords = "arkhe temporal frame record"))
    static FString RecordTemporalFrame(float DeltaTime);

    /** Get hash of a specific frame */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Get Frame Hash"))
    static FString GetFrameHash(int64 FrameNumber);

    /** Verify chain integrity */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Verify Temporal Chain"))
    static bool VerifyTemporalChain(int64 Start, int64 End);

    /** Export temporal chain to file */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Export Temporal Chain"))
    static bool ExportTemporalChain(FString FilePath);

    /** Get total registered frames */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Get Frame Count"))
    static int64 GetTemporalFrameCount();

    /** Get genesis block hash */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Get Genesis Hash"))
    static FString GetGenesisHash();

    /** Replay temporal chain */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Temporal Replay"))
    static void TemporalReplay(int64 Start, int64 End, float Speed = 1.0f);

    /** Generate Merkle proof for actor */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Generate Merkle Proof"))
    static TArray<uint8> GenerateProof(AActor* Actor, int64 Frame);

    /** Check causal safety of an action */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Check Causal Safety"))
    static bool CheckCausalSafety(FString Action, FString Target);

    /** Register causal link */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Register Causal Link"))
    static void RegisterCausalLink(FString Cause, FString Effect);

    /** Get temporal proof (ZK) */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Get Temporal Proof"))
    static TArray<uint8> GetTemporalProof(int64 Frame);

    /** Verify temporal proof */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Temporal",
        meta = (DisplayName = "Verify Temporal Proof"))
    static bool VerifyTemporalProof(int64 Frame, const TArray<uint8>& Proof);

    // =========================================================
    // SPATIAL NODES (10 nodes)
    // =========================================================

    /** Initialize spatial grid */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Initialize Spatial Grid"))
    static void InitializeSpatialGrid(float WorldSize);

    /** Find actors in radius */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Find Actors in Radius",
                WorldContext = "WorldContextObject"))
    static TArray<AActor*> FindActorsInRadius(UObject* WorldContextObject,
                                               FVector Center, float Radius);

    /** Find nearest actor */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Find Nearest Actor"))
    static AActor* FindNearestActor(FVector Point, float MaxDistance);

    /** Get actor neighbors */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Get Actor Neighbors"))
    static TArray<AActor*> GetNeighbors(AActor* Actor);

    /** World position to cell coordinate */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Spatial",
        meta = (DisplayName = "World to Cell"))
    static FIntVector WorldToCell(FVector WorldPos);

    /** Cell coordinate to world center */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Cell to World"))
    static FVector CellToWorld(FIntVector Cell);

    /** Spatial raycast */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Spatial Raycast",
                WorldContext = "WorldContextObject"))
    static bool SpatialRaycast(UObject* WorldContextObject,
                               FVector Start, FVector End, FHitResult& OutHit);

    /** Get registered actor count */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Get Registered Count"))
    static int32 GetRegisteredActorCount();

    /** Get occupied cell count */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Get Occupied Cells"))
    static int32 GetOccupiedCellCount();

    /** Update spatial grid */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial",
        meta = (DisplayName = "Update Spatial Grid"))
    static void UpdateSpatialGrid(float DeltaTime);

    // =========================================================
    // CONSCIOUSNESS NODES (8 nodes)
    // =========================================================

    /** Register consciousness agent */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Register Consciousness Agent"))
    static void RegisterAgent(APawn* Agent, FString PersonalitySeed = TEXT(""));

    /** Remove consciousness agent */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Unregister Agent"))
    static void UnregisterAgent(APawn* Agent);

    /** Agent perception query */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Agent Perceive"))
    static TArray<AActor*> AgentPerceive(APawn* Agent, float Radius);

    /** Get agent memory */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Get Agent Memory"))
    static FString GetAgentMemory(APawn* Agent);

    /** Trigger agent thought */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Agent Think"))
    static FString AgentThink(APawn* Agent, FString Stimulus);

    /** Set inference mode */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Set Inference Mode"))
    static void SetInferenceMode(TEnumAsByte<UArkheConsciousnessSubsystem::EArkheInferenceMode> Mode);

    /** Get active agent count */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Get Active Agent Count"))
    static int32 GetActiveAgentCount();

    /** Get agent emotional state */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Consciousness",
        meta = (DisplayName = "Get Agent Emotion"))
    static float GetAgentEmotion(APawn* Agent, FString Emotion);

    // =========================================================
    // Wasm NODES (8 nodes)
    // =========================================================

    /** Load Wasm module */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Load Wasm Module"))
    static bool LoadWasmModule(FString ModulePath, FString ModuleName);

    /** Unload Wasm module */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Unload Wasm Module"))
    static bool UnloadWasmModule(FString ModuleName);

    /** Call Wasm function */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Call Wasm Function"))
    static TArray<uint8> CallWasmFunction(FString ModuleName,
                                           FString FunctionName,
                                           TArray<uint8> Input);

    /** Check if module is loaded */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Is Wasm Module Loaded"))
    static bool IsModuleLoaded(FString ModuleName);

    /** Get loaded module list */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Get Loaded Modules"))
    static TArray<FString> GetLoadedModules();

    /** Execute Wasm code directly */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Execute Wasm"))
    static TArray<uint8> ExecuteWasm(TArray<uint8> WasmBinary,
                                      FString FunctionName,
                                      TArray<uint8> Input);

    /** Set Wasm memory limit */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Set Wasm Memory Limit"))
    static void SetWasmMemoryLimit(int32 Megabytes);

    /** Get Wasm module export list */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm",
        meta = (DisplayName = "Get Module Exports"))
    static TArray<FString> GetModuleExports(FString ModuleName);

    // =========================================================
    // META HUMAN NODES (6 nodes)
    // =========================================================

    /** Initialize MetaHuman ARKHE bridge */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|MetaHuman",
        meta = (DisplayName = "Init MetaHuman Bridge"))
    static void InitMetaHumanBridge(class USkeletalMeshComponent* MeshComponent);

    /** Get MetaHuman emotional blend shape value */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|MetaHuman",
        meta = (DisplayName = "Get Emotion Blend"))
    static float GetMetaHumanEmotion(class USkeletalMeshComponent* Mesh, FString Emotion);

    /** Set MetaHuman emotional state */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|MetaHuman",
        meta = (DisplayName = "Set MetaHuman Emotion"))
    static void SetMetaHumanEmotion(class USkeletalMeshComponent* Mesh,
                                     FString Emotion, float Intensity);

    /** Animate MetaHuman from ARKHE consciousness */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|MetaHuman",
        meta = (DisplayName = "Animate Consciousness"))
    static void AnimateConsciousness(class USkeletalMeshComponent* Mesh, APawn* Agent);

    /** Microexpression duration */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|MetaHuman",
        meta = (DisplayName = "Microexpression"))
    static void Microexpression(class USkeletalMeshComponent* Mesh,
                                 FString Expression, float Duration);

    /** Sync MetaHuman to consciousness state */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|MetaHuman",
        meta = (DisplayName = "Sync Consciousness to Face"))
    static void SyncFaceToConsciousness(class USkeletalMeshComponent* Mesh, APawn* Agent);

    // =========================================================
    // PROCEDURAL GENERATION NODES (4 nodes)
    // =========================================================

    /** Generate landscape from ARKHE seed */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Procedural",
        meta = (DisplayName = "Generate Landscape from Seed"))
    static class ULandscapeComponent* GenerateLandscape(int64 Seed,
                                                     int32 Size,
                                                     float Scale);

    /** Generate voxel grid from seed */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Procedural",
        meta = (DisplayName = "Generate Voxel Grid"))
    static class UArkheVoxelGrid* GenerateVoxelGrid(int64 Seed,
                                                       FVector Size);

    /** Generate flora from seed */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Procedural",
        meta = (DisplayName = "Generate Flora"))
    static TArray<AActor*> GenerateFlora(int64 Seed, FVector Area,
                                          TSubclassOf<AActor> PlantClass);

    /** Generate architecture from seed */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Procedural",
        meta = (DisplayName = "Generate Architecture"))
    static TArray<AActor*> GenerateArchitecture(int64 Seed,
                                                  FVector Location,
                                                  FVector Size);

    // =========================================================
    // UTILITY NODES (2 nodes)
    // =========================================================

    /** Compute ARKHE hash */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Utility",
        meta = (DisplayName = "ARKHE Hash"))
    static FString ComputeARKHEHash(const TArray<uint8>& Data);

    /** Version string */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Utility",
        meta = (DisplayName = "ARKHE Version"))
    static FString GetARKHEVersion();
};