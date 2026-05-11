#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Actor.h"
#include "ArkheNaniteBridge.generated.h"

/**
 * ARKHE Nanite Bridge — Procedural Voxel-to-Nanite Pipeline
 *
 * Converts ARKHE procedural voxel data into Nanite-optimized meshes.
 * Enables real-time terrain/sculpting with cryptographic provenance.
 */
UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class ARKHEUNREAL_API UArkheNaniteBridge : public UActorComponent
{
    GENERATED_BODY()

public:
    UArkheNaniteBridge();

    /** Generate Nanite mesh from ARKHE voxel data */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Nanite")
    class UProceduralMeshComponent* GenerateMeshFromSeed(int64 Seed);

    /** Update mesh in real-time (for dynamic terrain) */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Nanite")
    void ApplyTemporalDelta(const TArray<uint8>& DeltaData);

    /** Get LOD level for distance */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Nanite")
    int32 GetLODForDistance(float Distance) const;

    /** Mesh resolution scale */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARKHE|Nanite")
    float ResolutionScale;

    /** Enable Nanite fallback for complex meshes */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARKHE|Nanite")
    bool bEnableNaniteFallback;

    /** Maximum triangles per chunk */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARKHE|Nanite")
    int32 MaxTrianglesPerChunk;

protected:
    // Build vertex buffer from voxel grid
    void BuildFromVoxelGrid(class UArkheVoxelGrid* Grid);

    // Generate LOD chain
    void GenerateLODs(class UProceduralMeshComponent* Mesh, int32 NumLODs);

    // Nanite cluster optimization
    void OptimizeClusters(TArray<FVector>& Vertices,
                          TArray<int32>& Triangles);
};

/** Procedural mesh with ARKHE temporal data */
UCLASS()
class ARKHEUNREAL_API AArkheProceduralActor : public AActor
{
    GENERATED_BODY()

public:
    AArkheProceduralActor();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ARKHE|Nanite")
    class UProceduralMeshComponent* MeshComponent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARKHE|Nanite")
    UArkheNaniteBridge* NaniteBridge;

    /** Seed for generation */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ARKHE|Nanite")
    int64 GenerationSeed;

    virtual void OnConstruction(const FTransform& Transform) override;
};