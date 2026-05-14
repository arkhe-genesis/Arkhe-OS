; arkhe-os-full.iss
#define MyAppName "ARKHE OS Full Stack"
#define MyAppVersion "6.1.0"
#define MyAppPublisher "ARKHE OS Project"
#define MyAppURL "https://arkhe.global"
#define MyAppExeName "arkhed.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\ARKHE\OS
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE
OutputDir=.\
OutputBaseFilename=ArkheOS-Full-{#MyAppVersion}-Windows-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Add to PATH"; Flags: unchecked

[Files]
Source: "..\..\target\release\arkhed.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\arkhe-ws.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\arkhe-consciousness.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\phase-oracle.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\cmd\arkhe\arkhe.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs
Source: "..\..\dist\corvo-os\*"; DestDir: "{app}\corvo-os"; Flags: ignoreversion recursesubdirs
Source: "..\..\README.md"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  Path: String;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('addtopath') then
    begin
      Path := ExpandConstant('{app}');
      if not IsPathInEnv(Path) then
        AddToPathEnv(Path);
    end;
  end;
end;

function IsPathInEnv(const Path: String): Boolean;
var
  EnvPath: String;
begin
  EnvPath := GetEnv('PATH');
  Result := Pos(Path + ';', EnvPath) > 0;
end;

procedure AddToPathEnv(const Path: String);
var
  EnvPath: String;
begin
  EnvPath := GetEnv('PATH');
  if Pos(Path + ';', EnvPath) = 0 then
    SetEnv('PATH', Path + ';' + EnvPath, True);
end;
