// Copyright (c) 2026 ARKHE OS Collective. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "ArkheTemporalSubsystem.h"
#include "ArkheSpatialSubsystem.h"
#include "ArkheConsciousnessSubsystem.h"
#include "ArkheWasmSubsystem.h"
#include "ArkheMultiplayerSubsystem.h"
// #include "IAssetTools.h"
// #include "ToolMenus.h"

class FArkheUnrealModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;

    // Initialize ARKHE systems
    void InitializeTemporalSystem();
    void InitializeSpatialSystem();
    void InitializeWasmRuntime();
    void InitializeConsciousnessSystem();

    // Per-tick ARKHE update
    void OnWorldTickStart(ELevelTick TickType, float DeltaTime);
    void OnWorldTickEnd(ELevelTick TickType, float DeltaTime);

    // Wasm module management
    bool LoadWasmModule(const FString& ModulePath, const FString& ModuleName);
    bool UnloadWasmModule(const FString& ModuleName);
    TArray<uint8> ExecuteWasmFunction(const FString& ModuleName,
                                       const FString& FunctionName,
                                       const TArray<uint8>& Input);

    // Static access
    static FArkheUnrealModule& Get();

    class UArkheTemporalSubsystem* GetTemporalSystem() const { return TemporalSystem; }
    class UArkheSpatialSubsystem* GetSpatialSystem() const { return SpatialSystem; }
    class UArkheWasmSubsystem* GetWasmRuntime() const { return WasmRuntime; }
    class UArkheConsciousnessSubsystem* GetConsciousnessEngine() const { return ConsciousnessEngine; }

private:
    FDelegateHandle TickHandle;
    class UArkheTemporalSubsystem* TemporalSystem;
    class UArkheSpatialSubsystem* SpatialSystem;
    class UArkheWasmSubsystem* WasmRuntime;
    class UArkheConsciousnessSubsystem* ConsciousnessEngine;

    void RegisterMenus();
    void RegisterAssetTypes();
};

// Convenience macros
#define ARKHE_MODULE FArkheUnrealModule::Get()
#define ARKHE_TEMPORAL ARKHE_MODULE.GetTemporalSystem()
#define ARKHE_SPATIAL ARKHE_MODULE.GetSpatialSystem()
#define ARKHE_WASM ARKHE_MODULE.GetWasmRuntime()
#define ARKHE_CONSCIOUSNESS ARKHE_MODULE.GetConsciousnessEngine()
