#define MyAppName "Campo Burger POS"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Campo Burger"
#define MyAppExeName "CampoBurgerPOS.exe"


; ================================================================
; CAMPO BURGER POS
; INSTALADOR WINDOWS
; ================================================================


[Setup]

AppId={{A3A18D6C-4827-4F94-AF97-6C9D2B4E1701}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Campo Burger POS
DefaultGroupName={#MyAppName}

DisableProgramGroupPage=yes

; El .iss ya se encuentra dentro de installer,
; por eso el resultado se genera en esta misma carpeta.
OutputDir=.

OutputBaseFilename=CampoBurgerPOS_Setup

SetupIconFile=..\campo_burger.ico

UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes

WizardStyle=modern

PrivilegesRequired=admin

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

CloseApplications=yes


; ================================================================
; ARCHIVOS DEL CLIENTE
; ================================================================

[Files]

Source: "..\dist\CampoBurgerPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


; ================================================================
; ACCESOS DIRECTOS
; ================================================================

[Icons]

Name: "{autodesktop}\Campo Burger POS"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"

Name: "{autoprograms}\Campo Burger POS"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"


; ================================================================
; EJECUTAR DESPUES DE INSTALAR
; ================================================================

[Run]

Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Campo Burger POS"; Flags: nowait postinstall skipifsilent