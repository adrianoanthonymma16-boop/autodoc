; =============================================================================
; AutoDoc — Instalador Windows (Inno Setup 6)
; Compilar com: ISCC.exe /DAppVersion=4.0.0 autodoc.iss
; =============================================================================

#ifndef AppVersion
  #define AppVersion "4.0.0"
#endif

#define AppName "AutoDoc"
#define AppPublisher "Adriano Anthony"
#define AppExe "AutoDoc.exe"
#define ProjectRoot "..\.."

[Setup]
AppId={{8E4C1B60-3C7E-4B0E-9C1D-A7D6C2F0E1B4}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/adrianoanthonymma16-boop/autodoc
AppSupportURL=https://github.com/adrianoanthonymma16-boop/autodoc/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
OutputDir={#ProjectRoot}\dist
OutputBaseFilename=autodoc-ctk_{#AppVersion}_win64_setup
SetupIconFile={#ProjectRoot}\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
CloseApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#ProjectRoot}\dist\AutoDoc\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
