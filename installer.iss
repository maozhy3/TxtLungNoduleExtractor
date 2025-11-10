; Inno Setup 安装脚本
; 用于创建医疗影像报告预测工具的安装程序

#define MyAppName "医疗影像报告预测工具"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Organization"
#define MyAppExeName "医疗影像报告预测工具.exe"

[Setup]
; 应用信息
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 输出设置
OutputDir=installer_output
OutputBaseFilename={#MyAppName}_v{#MyAppVersion}_安装包
; 压缩
Compression=lzma2/max
SolidCompression=yes
; 界面
WizardStyle=modern
; 权限
PrivilegesRequired=admin
; 架构
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 主程序文件
Source: "dist\{#MyAppName}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 注意：模型文件需要手动复制到 dist\医疗影像报告预测工具\models\ 目录

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; 首次运行时安装 VC++ 运行库
Filename: "{app}\_vcredist\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "正在安装 Microsoft Visual C++ 运行库..."; Flags: waituntilterminated skipifdoesntexist
; 安装完成后询问是否运行
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时删除生成的文件
Type: filesandordirs; Name: "{app}\checkpoints"
Type: files; Name: "{app}\*.xlsx"
Type: files; Name: "{app}\config.py"
