@echo off
setlocal enabledelayedexpansion

echo ╔═══════════════════════════════════════════════════════╗
echo ║  ARKHE × Unreal Engine Plugin — Build System        ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: Configuration
set UE_ROOT=%UNREAL_ENGINE_PATH%
set PROJECT_DIR=%CD%
set WASM_TARGET=%PROJECT_DIR%\Native\rust\target
set PLUGIN_DIR=%PROJECT_DIR%\Plugins\Runtime\ArkhePlugin

:: Step 1: Build Rust Wasm
echo.
echo [1/4] Building Rust Wasm module...
cd /d "%PROJECT_DIR%\Native\rust"
cargo build --target wasm32-wasi --release
if errorlevel 1 (
    echo ERROR: Rust build failed
    goto :error
)
copy /y "target\wasm32-wasi\release\arkhe_ue_wasm.wasm" "%PLUGIN_DIR%\Scripts\arkhe_core.wasm"
echo    ✓ Wasm module built

:: Step 2: Generate bindings
echo.
echo [2/4] Generating UE bindings...
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    goto :error
)
python "%PROJECT_DIR%\Scripts\GenerateBindings.py"
echo    ✓ Bindings generated

:: Step 3: Build UE plugin
echo.
echo [3/4] Building Unreal plugin...
cd /d "%UE_ROOT%"
Engine\Build\BatchFiles\RunUAT.bat BuildPlugin ^
    -Plugin="%PROJECT_DIR%\ArkheUnreal.uplugin" ^
    -Package="%PLUGIN_DIR%" ^
    -Rocket
if errorlevel 1 (
    echo ERROR: UE build failed
    goto :error
)
echo    ✓ UE plugin built

:: Step 4: Verify
echo.
echo [4/4] Verification...
if not exist "%PLUGIN_DIR%\Binaries\Win64\ArkheUnreal.dll" (
    echo ERROR: DLL not found
    goto :error
)
echo    ✓ All artifacts generated

echo.
echo ════════════════════════════════════════════════════════
echo    BUILD SUCCESS
echo    Plugin location: %PLUGIN_DIR%
echo ════════════════════════════════════════════════════════

goto :eof

:error
echo ERROR ENCOUNTERED!
endlocal