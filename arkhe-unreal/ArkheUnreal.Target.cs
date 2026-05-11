// Copyright (c) 2026 ARKHE OS Collective. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class ArkheUnrealTarget : TargetRules
{
    public ArkheUnrealTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V2;

        ExtraModuleNames.AddRange(new string[] {
            "ArkheUnreal",
            "ArkheWasmRuntime",
            "ArkheUnrealEditor",
        });

        // Enable required features
        bBuildWithPluginSupport = true;
        bCompileSimplygon = false;
        bBuildDeveloperTools = true;
        bBuildEditor = true;
        bBuildRequiresCookedData = true;
        bBuildMeshSimplifier = true;
    }
}