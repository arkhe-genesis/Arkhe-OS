#include "ArkheSpatialSubsystem.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Components/PrimitiveComponent.h"

// DECLARE LOG CATEGORY
DECLARE_LOG_CATEGORY_EXTERN(LogArkhe, Log, All);

UArkheSpatialSubsystem::UArkheSpatialSubsystem()
    : OccupiedCellCount(0)
    , RegisteredActorCount(0)
    , CellSize(500.0f) // 5m default cell
{
}

void UArkheSpatialSubsystem::Initialize(float WorldSize)
{
    CellSize = FMath::Max(WorldSize / 2048.0f, 100.0f);
    OccupiedCellCount = 0;
    RegisteredActorCount = 0;
    SpatialGrid.Empty();
    ActorLocations.Empty();

    // UE_LOG(LogArkhe, Log, TEXT("🌐 Spatial Hash initialized: CellSize=%.0f, WorldSize=%.0f"),
    //    CellSize, WorldSize);
}

void UArkheSpatialSubsystem::RegisterActor(AActor* Actor)
{
    if (!Actor) return;

    FIntVector Cell = WorldToCell(Actor->GetActorLocation());
    TWeakObjectPtr<AActor> WeakActor(Actor);

    // Remove from old cell if moving
    if (ActorLocations.Contains(WeakActor))
    {
        FIntVector OldCell = ActorLocations[WeakActor];
        if (OldCell != Cell)
        {
            if (SpatialGrid.Contains(OldCell))
            {
                SpatialGrid[OldCell].Remove(WeakActor);
                if (SpatialGrid[OldCell].Num() == 0)
                {
                    SpatialGrid.Remove(OldCell);
                    OccupiedCellCount--;
                }
            }
        }
    }

    // Add to new cell
    if (!SpatialGrid.Contains(Cell))
    {
        SpatialGrid.Add(Cell);
        OccupiedCellCount++;
    }

    if (!SpatialGrid[Cell].Contains(WeakActor))
    {
        SpatialGrid[Cell].Add(WeakActor);
        RegisteredActorCount++;
    }

    ActorLocations.Add(WeakActor, Cell);
}

void UArkheSpatialSubsystem::UnregisterActor(AActor* Actor)
{
    if (!Actor) return;

    TWeakObjectPtr<AActor> WeakActor(Actor);

    if (!ActorLocations.Contains(WeakActor))
        return;

    FIntVector Cell = ActorLocations[WeakActor];

    if (SpatialGrid.Contains(Cell))
    {
        SpatialGrid[Cell].Remove(WeakActor);
        if (SpatialGrid[Cell].Num() == 0)
        {
            SpatialGrid.Remove(Cell);
            OccupiedCellCount--;
        }
    }

    ActorLocations.Remove(WeakActor);
    RegisteredActorCount--;
}

TArray<AActor*> UArkheSpatialSubsystem::FindActorsInRadius(FVector Center, float Radius) const
{
    TArray<AActor*> Result;

    // Determine cell range
    int32 CellRange = FMath::CeilToInt(Radius / CellSize);
    FIntVector CenterCell = WorldToCell(Center);

    for (int32 X = -CellRange; X <= CellRange; X++)
    {
        for (int32 Y = -CellRange; Y <= CellRange; Y++)
        {
            for (int32 Z = -CellRange; Z <= CellRange; Z++)
            {
                FIntVector Cell = CenterCell + FIntVector(X, Y, Z);

                if (SpatialGrid.Contains(Cell))
                {
                    for (const TWeakObjectPtr<AActor>& WeakActor : SpatialGrid[Cell])
                    {
                        if (AActor* Actor = WeakActor.Get())
                        {
                            float Dist = FVector::Dist(Center, Actor->GetActorLocation());
                            if (Dist <= Radius)
                            {
                                Result.Add(Actor);
                            }
                        }
                    }
                }
            }
        }
    }

    return Result;
}

AActor* UArkheSpatialSubsystem::FindNearestActor(FVector Point, float MaxDistance) const
{
    AActor* Nearest = nullptr;
    float MinDist = MaxDistance;

    int32 CellRange = FMath::CeilToInt(MaxDistance / CellSize);
    FIntVector CenterCell = WorldToCell(Point);

    for (int32 X = -CellRange; X <= CellRange; X++)
    {
        for (int32 Y = -CellRange; Y <= CellRange; Y++)
        {
            for (int32 Z = -CellRange; Z <= CellRange; Z++)
            {
                FIntVector Cell = CenterCell + FIntVector(X, Y, Z);

                if (SpatialGrid.Contains(Cell))
                {
                    for (const TWeakObjectPtr<AActor>& WeakActor : SpatialGrid[Cell])
                    {
                        if (AActor* Actor = WeakActor.Get())
                        {
                            float Dist = FVector::Dist(Point, Actor->GetActorLocation());
                            if (Dist < MinDist)
                            {
                                MinDist = Dist;
                                Nearest = Actor;
                            }
                        }
                    }
                }
            }
        }
    }

    return Nearest;
}

TArray<AActor*> UArkheSpatialSubsystem::GetNeighbors(AActor* Actor) const
{
    if (!Actor) return TArray<AActor*>();
    return FindActorsInRadius(Actor->GetActorLocation(), CellSize * 2.0f);
}

bool UArkheSpatialSubsystem::SpatialRaycast(FVector Start, FVector End, FHitResult& OutHit) const
{
    // Use UE's built-in raycast but with spatial hash for broadphase
    FCollisionQueryParams Params;
    Params.AddIgnoredActor(nullptr);

    UWorld* World = GetWorld();
    if (!World) return false;

    // First, narrow down to cells along the ray
    FVector Direction = (End - Start).GetSafeNormal();
    float Length = FVector::Dist(Start, End);

    // Quick broadphase using spatial grid
    TArray<AActor*> Candidates = FindActorsInRadius(
        (Start + End) / 2.0f, Length);

    // Precise raycast against candidates
    AActor* HitActor = nullptr;
    float MinDist = MAX_FLT;

    for (AActor* Candidate : Candidates)
    {
        if (!Candidate) continue;

        FVector HitLoc, HitNormal;
        if (Candidate->ActorLineTraceSingle(HitLoc, HitNormal, Start, End,
            ECollisionChannel::ECC_Visibility, false))
        {
            float Dist = FVector::Dist(Start, HitLoc);
            if (Dist < MinDist)
            {
                MinDist = Dist;
                HitActor = Candidate;
                OutHit.Location = HitLoc;
                OutHit.Normal = HitNormal;
                OutHit.Actor = Candidate;
            }
        }
    }

    return HitActor != nullptr;
}

FIntVector UArkheSpatialSubsystem::WorldToCell(FVector WorldPos) const
{
    return FIntVector(
        FMath::FloorToInt(WorldPos.X / CellSize),
        FMath::FloorToInt(WorldPos.Y / CellSize),
        FMath::FloorToInt(WorldPos.Z / CellSize)
    );
}

FVector UArkheSpatialSubsystem::CellToWorld(FIntVector Cell) const
{
    return FVector(
        (Cell.X + 0.5f) * CellSize,
        (Cell.Y + 0.5f) * CellSize,
        (Cell.Z + 0.5f) * CellSize
    );
}

uint32 UArkheSpatialSubsystem::HashCell(const FIntVector& Cell) const
{
    // Simple spatial hash
    return (Cell.X * 73856093) ^ (Cell.Y * 19349663) ^ (Cell.Z * 83492791);
}

void UArkheSpatialSubsystem::UpdateSpatialQueries(float DeltaTime)
{
    // Periodically rebuild spatial grid for moved actors
    static float Accumulator = 0.0f;
    Accumulator += DeltaTime;

    if (Accumulator >= 0.1f) // Update every 100ms
    {
        Accumulator = 0.0f;

        // Re-register all actors (handles movement)
        TArray<FIntVector> CellsToRemove;
        for (auto& Pair : SpatialGrid)
        {
            // Check if actors still belong to their cells
            for (int32 i = Pair.Value.Num() - 1; i >= 0; i--)
            {
                if (AActor* Actor = Pair.Value[i].Get())
                {
                    FIntVector CurrentCell = WorldToCell(Actor->GetActorLocation());
                    if (CurrentCell != Pair.Key)
                    {
                        // Actor moved to different cell
                        Pair.Value.RemoveAtSwap(i);
                        RegisterActor(Actor);
                    }
                }
            }
        }
    }
}