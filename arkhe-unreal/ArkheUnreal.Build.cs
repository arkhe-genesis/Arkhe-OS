// Copyright (c) 2026 ARKHE OS Collective. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class ArkheUnreal : ModuleRules
{
    public ArkheUnreal(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        bEnableExceptions = true;
        bUseUnity = true;
        bFasterWithoutUnity = true;

        // C++ Standard
        CppStandard = CppStandardVersion.Cpp17;

        // Public include paths
        PublicIncludePaths.AddRange(new string[] {
            Path.Combine(ModuleDirectory, "Public"),
            Path.Combine(ModuleDirectory, "Native", "Public"),
            Path.Combine(ModuleDirectory, "ThirdParty", "wasmtime", "Include"),
            Path.Combine(ModuleDirectory, "..", "arkhe-core", "include"),
        });

        // Private include paths
        PrivateIncludePaths.AddRange(new string[] {
            Path.Combine(ModuleDirectory, "Private"),
            Path.Combine(ModuleDirectory, "Native", "Private"),
        });

        // Public dependency modules
        PublicDependencyModuleNames.AddRange(new string[] {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "RHI",
            "RenderCore",
            "ShaderCore",
            "UnrealEd",
            "Serialization",
            "Networking",
            "Sockets",
            "Json",
            "JsonUtilities",
            "HTTP",
            "MeshDescription",
            "StaticMeshEditor",
            "GeometryFramework",
        });

        // Private dependency modules
        PrivateDependencyModuleNames.AddRange(new string[] {
            "Slate",
            "SlateCore",
            "EditorStyle",
            "AssetTools",
            "MessageLog",
            "UnrealEdMessages",
            "BlueprintGraph",
            "GraphEditor",
            "Kismet",
            "KismetCompiler",
            "AIModule",
            "NavigationSystem",
            "GameplayTasks",
            "Niagara",
        });

        // Dynamically loaded modules
        DynamicallyLoadedModuleNames.AddRange(new string[] {
            "HTTP",
            "SSL",
        });

        // Wasmtime library
        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            string WasmtimePath = Path.Combine(ModuleDirectory, "ThirdParty", "wasmtime", "Lib", "Win64");
            PublicAdditionalLibraries.Add(Path.Combine(WasmtimePath, "wasmtime.lib"));
            RuntimeDependencies.Add(Path.Combine(WasmtimePath, "wasmtime.dll"));
        }
        else if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            string WasmtimePath = Path.Combine(ModuleDirectory, "ThirdParty", "wasmtime", "Lib", "Linux");
            PublicAdditionalLibraries.Add(Path.Combine(WasmtimePath, "libwasmtime.a"));
        }
        else if (Target.Platform == UnrealTargetPlatform.Mac)
        {
            string WasmtimePath = Path.Combine(ModuleDirectory, "ThirdParty", "wasmtime", "Lib", "Mac");
            PublicAdditionalLibraries.Add(Path.Combine(WasmtimePath, "libwasmtime.a"));
        }

        // Rust FFI library
        string RustLibPath = Path.Combine(ModuleDirectory, "Native", "rust", "target");
        if (Target.Configuration == UnrealTargetConfiguration.Shipping)
            RustLibPath = Path.Combine(RustLibPath, "release");
        else
            RustLibPath = Path.Combine(RustLibPath, "debug");

        if (Target.Platform == UnrealTargetPlatform.Win64)
            PublicAdditionalLibraries.Add(Path.Combine(RustLibPath, "arkhe_wasm_bridge.lib"));
        else if (Target.Platform == UnrealTargetPlatform.Linux)
            PublicAdditionalLibraries.Add(Path.Combine(RustLibPath, "libarkhe_wasm_bridge.a"));
        else if (Target.Platform == UnrealTargetPlatform.Mac)
            PublicAdditionalLibraries.Add(Path.Combine(RustLibPath, "libarkhe_wasm_bridge.a"));

        // Compiler definitions
        PublicDefinitions.Add("ARKHE_UNREAL=1");
        PublicDefinitions.Add("ARKHE_VERSION=L\"6.0.0\"");
        PublicDefinitions.Add("ARKHE_TEMPORAL_ENABLED=1");
        PublicDefinitions.Add("ARKHE_SPATIAL_ENABLED=1");
        PublicDefinitions.Add("ARKHE_CONSCIOUSNESS_ENABLED=1");

        if (Target.Configuration == UnrealTargetConfiguration.Debug)
        {
            PublicDefinitions.Add("ARKHE_DEBUG=1");
            PublicDefinitions.Add("ARKHE_VALIDATION=1");
        }

        // Runtime mesh support
        PublicDefinitions.Add("ARKHE_NANITE_BRIDGE=1");
        PublicDefinitions.Add("ARKHE_VOXEL_GRID=1");

        // Optimize for shipping
        if (Target.Configuration == UnrealTargetConfiguration.Shipping)
        {
            PublicDefinitions.Add("ARKHE_SHIPPING=1");
            PublicDefinitions.Add("NDEBUG=1");
            bOptimizeCode = true;
        }
    }
}