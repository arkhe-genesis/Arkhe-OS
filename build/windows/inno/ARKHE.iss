; ARKHE OS — Inno Setup Script
; Compile with: iscc ARKHE.iss

[Setup]
AppName=ARKHE OS
AppVersion=6.1.0
AppPublisher=ARKHE Foundation
DefaultDirName={autopf}\ARKHE OS
DefaultGroupName=ARKHE OS
UninstallDisplayIcon={app}\bin\arkhe.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.\output
OutputBaseFilename=ARKHE-OS-6.1.0-win64
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
LicenseFile=..\..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Types]
Name: "full"; Description: "Full installation (all services, models, CORVO OS)"
Name: "core"; Description: "Core services + CLI only"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "core"; Description: "ARKHE Core (CLI + Daemons)"; Types: full core custom; Flags: fixed
Name: "corvo"; Description: "CORVO OS live-build artifacts"; Types: full
Name: "models"; Description: "Neural & Quantum Model Weights (~250GB)"; Types: full
Name: "python"; Description: "Python Runtime & Libraries"; Types: full core
Name: "docs"; Description: "Documentation"; Types: full

[Files]
; Core binaries
Source: "..\..\target\release\arkhe.exe"; DestDir: "{app}\bin"; Components: core
Source: "..\..\target\release\arkhed.exe"; DestDir: "{app}\bin"; Components: core
Source: "..\..\target\release\arkhe-ws.exe"; DestDir: "{app}\bin"; Components: core
Source: "..\..\target\release\arkhe-consciousness.exe"; DestDir: "{app}\bin"; Components: core
Source: "..\..\target\release\phase-oracle.exe"; DestDir: "{app}\bin"; Components: core

; Python
Source: "..\..\bridges\x402\x402_pix_bridge.py"; DestDir: "{app}\share\python"; Components: python
Source: "..\..\bindings\python\qart.py"; DestDir: "{app}\share\python"; Components: python
Source: "..\..\arkhe_core\temporal_network.py"; DestDir: "{app}\share\python"; Components: python

; CORVO OS
Source: "..\..\corvo\live-build\artifacts\*"; DestDir: "{app}\share\corvo"; Components: corvo; Flags: recursesubdirs

; Models (these should be tracked with Git LFS)
Source: "..\..\data\models\*"; DestDir: "{app}\share\models"; Components: models; Flags: recursesubdirs

; Documentation
Source: "..\..\docs\*"; DestDir: "{app}\docs"; Components: docs; Flags: recursesubdirs

; Configuration
Source: "..\..\config\arkhe.toml"; DestDir: "{app}\etc"; Components: core

[Icons]
Name: "{group}\ARKHE CLI"; Filename: "{app}\bin\arkhe.exe"; WorkingDir: "{app}"
Name: "{group}\ARKHE Documentation"; Filename: "{app}\docs\README.md"
Name: "{group}\Uninstall ARKHE OS"; Filename: "{uninstallexe}"
Name: "{commondesktop}\ARKHE CLI"; Filename: "{app}\bin\arkhe.exe"; Tasks: desktopicon; WorkingDir: "{app}"

[Registry]
Root: HKLM; Subkey: "SOFTWARE\ARKHE OS Foundation\ARKHE OS"; ValueType: string; ValueName: "Version"; ValueData: "6.1.0"
Root: HKLM; Subkey: "SOFTWARE\ARKHE OS Foundation\ARKHE OS"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Services\ARKHE"; ValueType: dword; ValueName: "DelayedAutostart"; ValueData: 1

[Run]
Filename: "{app}\bin\arkhed.exe"; Parameters: "--install"; Flags: runhidden
Filename: "{app}\docs\README.md"; Description: "View main documentation"; Flags: postinstall shellexec skipifsilent

[Code]
function InitializeSetup: Boolean;
begin
  if not Is64BitInstallMode then begin
    MsgBox('ARKHE OS requires a 64-bit Windows system.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  Result := True;
end;