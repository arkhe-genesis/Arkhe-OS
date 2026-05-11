#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ArkheWasmSubsystem.generated.h"

/**
 * ARKHE Wasm Runtime — Sandboxed Module Execution
 *
 * Executes Wasm modules within UE for:
 *   - Custom AI decision making
 *   - Procedural generation algorithms
 *   - Physics simulations
 *   - Any compute task requiring isolation
 *
 * Wasm modules are loaded from Content/WasmModules/
 */
UCLASS(BlueprintType, Blueprintable)
class ARKHEUNREAL_API UArkheWasmSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UArkheWasmSubsystem();

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    /** Load a Wasm module from file */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm")
    bool LoadModule(const FString& ModulePath, const FString& ModuleName);

    /** Unload a Wasm module */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm")
    bool UnloadModule(const FString& ModuleName);

    /** Execute a Wasm function */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm")
    TArray<uint8> CallFunction(const FString& ModuleName, const FString& FunctionName,
                                const TArray<uint8>& Input = TArray<uint8>());

    /** Check if module is loaded */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm")
    bool IsModuleLoaded(const FString& ModuleName) const;

    /** Get list of loaded modules */
    UFUNCTION(BlueprintCallable, Category = "ARKHE|Wasm")
    TArray<FString> GetLoadedModules() const;

    /** Get number of loaded modules */
    UPROPERTY(BlueprintReadOnly, Category = "ARKHE|Wasm")
    int32 LoadedModuleCount;

    /** Maximum module memory (MB) */
    UPROPERTY(BlueprintReadWrite, Category = "ARKHE|Wasm")
    int32 MaxMemoryMB;

    /** Maximum execution time per call (ms) */
    UPROPERTY(BlueprintReadWrite, Category = "ARKHE|Wasm")
    int32 MaxExecutionTimeMs;

    // Add LoadAllFromDirectory and TickAll
    void LoadAllFromDirectory(const FString& Directory);
    void TickAll(float DeltaTime);

protected:
    // Internal Wasm runtime handle
    void* WasmRuntimeHandle;

    // Module registry
    TMap<FString, void*> LoadedModules;

    // Initialize Wasmtime engine
    bool InitializeWasmtime();

    // Create sandboxed instance
    void* CreateSandboxedInstance(const FString& ModulePath);
};