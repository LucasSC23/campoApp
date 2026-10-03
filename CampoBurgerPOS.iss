#define MyAppName "Campo Burger POS"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Campo Burger"
#define MyAppExeName "CampoBurgerPOS.exe"


; ================================================================
; CONFIGURACION GENERAL DEL INSTALADOR
; ================================================================

[Setup]

AppId={{A3A18D6C-4827-4F94-AF97-6C9D2B4E1701}

AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Campo Burger POS
DefaultGroupName={#MyAppName}

DisableProgramGroupPage=yes

OutputDir=installer
OutputBaseFilename=CampoBurgerPOS_Setup

SetupIconFile=campo_burger.ico

UninstallDisplayIcon={app}\{#MyAppExeName}

Compression=lzma2
SolidCompression=yes

WizardStyle=modern

PrivilegesRequired=admin

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

CloseApplications=yes


; ================================================================
; ARCHIVOS DEL PROGRAMA
; ================================================================

[Files]

Source: "dist\CampoBurgerPOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs


; ================================================================
; ACCESOS DIRECTOS
; ================================================================

[Icons]

Name: "{autodesktop}\Campo Burger POS"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"

Name: "{autoprograms}\Campo Burger POS"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"


; ================================================================
; EJECUTAR AL FINALIZAR INSTALACION
; ================================================================

[Run]

Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Campo Burger POS"; Flags: nowait postinstall skipifsilent