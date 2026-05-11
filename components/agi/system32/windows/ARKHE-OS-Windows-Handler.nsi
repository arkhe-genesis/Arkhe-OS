; ARKHE-OS-Windows-Handler.nsi
Name "ARKHE OS .agi Handler"
OutFile "ARKHE-OS-AGI-Handler-Setup.exe"
InstallDir "$PROGRAMFILES\ARKHE OS"
RequestExecutionLevel admin

Section "Install"
    SetOutPath $INSTDIR
    File "agictl.exe"
    File "arkhe-icon.ico"
    File "arkhe-agi-assoc.reg"

    ; Executar registro silenciosamente
    ExecWait '"regedit.exe" /s "$INSTDIR\arkhe-agi-assoc.reg"'

    ; Criar atalho no Menu Iniciar
    CreateShortCut "$SMPROGRAMS\ARKHE OS.lnk" "$INSTDIR\agictl.exe"
SectionEnd