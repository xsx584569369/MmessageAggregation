; 芯讯 · 存储芯片资讯台 —— Inno Setup 安装包脚本
; 用法（Windows，已装 Inno Setup）：先跑 build_win.bat 出 dist\ChipNews\，再执行  iscc installer.iss
; 说明：用户数据存放在 %LOCALAPPDATA%\ChipNews，卸载不会删除（已抓取的消息/配置保留）。

#define AppName "芯讯 · 存储芯片资讯台"
#ifndef AppVer
  #define AppVer "1.0.0"
#endif
#define ExeName "ChipNews.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher=ChipNews
DefaultDirName={autopf}\ChipNews
DefaultGroupName=芯讯
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#ExeName}
OutputDir=installer_output
OutputBaseFilename=芯讯_安装包_v{#AppVer}
SetupIconFile=icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=admin

[Languages]
Name: "cn"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："

[Files]
Source: "dist\ChipNews\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\芯讯"; Filename: "{app}\{#ExeName}"
Name: "{group}\卸载芯讯"; Filename: "{uninstallexe}"
Name: "{autodesktop}\芯讯"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "立即运行芯讯"; Flags: nowait postinstall skipifsilent
