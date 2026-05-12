[Setup]
AppName=ARKHE OS
AppVersion=6.1.0
AppPublisher=Arkhe Network
DefaultDirName={pf}\ARKHE OS
DefaultGroupName=ARKHE OS
OutputBaseFilename=arkhe_setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\..\cmd\arkhe\arkhe.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\arkhed.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\arkhe-ws.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\arkhe-consciousness.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\target\release\phase-oracle.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\python_components\*"; DestDir: "{app}\python_components"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\ARKHE OS CLI"; Filename: "{app}\arkhe.exe"
Name: "{group}\ARKHE Daemon"; Filename: "{app}\arkhed.exe"
