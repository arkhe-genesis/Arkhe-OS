#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ArkheSpatialSubsystem.generated.h"

/**
 * ARKHE Spatial Hash — O(1) 3D Spatial Queries
 *
 * Divides the world into cubic cells and indexes all actors
 * for rapid spatial queries (neighbors, collisions, proximity).
 *
 * Used by:
 *   - NPC consciousness (what can an AI agent perceive?)
 *   - Physics interactions (spatial broadphase)
 *   - Procedural generation (seeded voxel placement)
 *   - Temporal chain (spatial component of temporal blocks)
 */
UCLASS(BlueprintType, Blueprintable)
class ARKHEUNREAL_API UArkheSpatialSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UArkheSpatialSubsystem();

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /** Initialize spatial grid with given cell size */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    void Initialize(float WorldSize);

    /** Register an actor in the spatial hash */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    void RegisterActor(AActor* Actor);

    /** Remove an actor from spatial hash */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    void UnregisterActor(AActor* Actor);

    /** Find all actors within radius of a point */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    TArray<AActor*> FindActorsInRadius(FVector Center, float Radius) const;

    /** Find nearest actor to a point */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    AActor* FindNearestActor(FVector Point, float MaxDistance = 10000.0f) const;

    /** Get all actors in neighboring cells */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    TArray<AActor*> GetNeighbors(AActor* Actor) const;

    /** Raycast through spatial hash (fast) */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Spatial")
    bool SpatialRaycast(FVector Start, FVector End, FHitResult& OutHit) const;

    /** Get cell coordinate for a world position */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Spatial")
    FIntVector WorldToCell(FVector WorldPos) const;

    /** Get world center of a cell */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ARKHE|Spatial")
    FVector CellToWorld(FIntVector Cell) const;

    /** Get number of occupied cells */
    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Spatial")
    int32 OccupiedCellCount;

    /** Get total registered actors */
    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Spatial")
    int32 RegisteredActorCount;

    /** Grid cell size in unreal units */
    UPROPERTY(BlueprintReadWrite, Category = "ARKHE|Spatial")
    float CellSize;

protected:
    // Spatial hash: cell coordinate → list of actors
    TMap<FIntVector, TArray<TWeakObjectPtr<AActor>>> SpatialGrid;

    // Actor → cell mapping for fast removal
    TMap<TWeakObjectPtr<AActor>, FIntVector> ActorLocations;

    // Hash function for cell coordinates
    uint32 HashCell(const FIntVector& Cell) const;
};