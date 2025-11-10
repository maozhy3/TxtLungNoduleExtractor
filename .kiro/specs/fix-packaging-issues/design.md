# Design Document

## Overview

This design addresses 10 critical packaging issues identified in the medical imaging report prediction tool. The solution focuses on making the build system portable, robust, and user-friendly while integrating all fixes into the existing README.md documentation rather than creating separate files.

The design follows a minimal-change approach to preserve existing functionality while fixing critical bugs that prevent builds on different machines and cause runtime failures.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Build System Layer                        │
├─────────────────────────────────────────────────────────────┤
│  gui.spec  │  main.spec  │  hook-conda-pack.py  │  build_gui.bat │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
├─────────────────────────────────────────────────────────────┤
│  gui.py  │  main.py  │  core.py  │  config.py  │  config_loader.py │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Runtime Environment                         │
├─────────────────────────────────────────────────────────────┤
│  Checkpoint Manager  │  Path Resolver  │  VC++ Installer     │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Portability First**: All paths must be relative or dynamically resolved
2. **Fail Gracefully**: Provide clear error messages instead of cryptic failures
3. **Minimal Changes**: Fix bugs without restructuring working code
4. **Documentation Integration**: Add fixes to README.md, not separate docs
5. **Backward Compatible**: Existing configurations should continue to work

## Components and Interfaces

### 1. Spec File Improvements

#### gui.spec and main.spec

**Current Issues**:
- main.spec has hardcoded absolute paths
- Inconsistent hiddenimports between files
- Missing critical dependencies

**Design Solution**:

```python
# Dynamic path resolution pattern
import os
from pathlib import Path

# Get spec file directory
spec_root = Path(SPECPATH)

# Use relative paths
a = Analysis(
    ['gui.py'],  # or ['main.py']
    pathex=[],
    binaries=[],
    datas=[
        (str(spec_root / 'config.py'), '.'),  # Include config as data
    ],
    hiddenimports=[
        # Standard library
        'pickle',
        'concurrent.futures',
        'importlib.util',
        'pathlib',
        'subprocess',
        'threading',
        # Third-party
        'pandas',
        'openpyxl',
        'llama_cpp',
        'tqdm',
        'tkinter',  # GUI only
    ],
    hookspath=[str(spec_root)],  # Relative hook path
    ...
)
```

**Key Changes**:
- Use `SPECPATH` variable (PyInstaller built-in) for relative paths
- Unified hiddenimports list for both spec files
- Include config.py as data file
- Remove hardcoded user paths

### 2. Hook File Enhancement

#### hook-conda-pack.py

**Current Issues**:
- Only collects pandas 'core' subdirectory
- Missing openpyxl data collection
- No error handling

**Design Solution**:

```python
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = []
binaries = []

# Collect llama_cpp binaries (existing, keep as-is)
try:
    binaries += collect_dynamic_libs('llama_cpp')
except Exception as e:
    print(f"Warning: Could not collect llama_cpp binaries: {e}")

# Collect pandas data (remove subdir restriction)
try:
    datas += collect_data_files('pandas')
except Exception as e:
    print(f"Warning: Could not collect pandas data: {e}")

# Add openpyxl data collection
try:
    datas += collect_data_files('openpyxl')
except Exception as e:
    print(f"Warning: Could not collect openpyxl data: {e}")

# Collect tqdm data (existing, keep as-is)
try:
    datas += collect_data_files('tqdm')
except Exception as e:
    print(f"Warning: Could not collect tqdm data: {e}")
```

**Key Changes**:
- Remove `subdir='core'` restriction from pandas
- Add openpyxl data collection
- Wrap each collection in try-except for graceful failures
- Add warning messages for debugging

### 3. Checkpoint Directory Safety

#### core.py - CheckpointManager

**Current Issues**:
- Creates checkpoint directory in current working directory
- May fail in restricted permissions environments
- No fallback mechanism

**Design Solution**:

```python
import tempfile
from pathlib import Path

class CheckpointManager:
    def __init__(self, checkpoint_dir: Path = None, save_interval: int = 10):
        if checkpoint_dir is None:
            # Try multiple locations in order of preference
            checkpoint_dir = self._get_safe_checkpoint_dir()
        
        self.checkpoint_dir = checkpoint_dir
        self.save_interval = save_interval
        self._ensure_directory()
    
    def _get_safe_checkpoint_dir(self) -> Path:
        """Get a safe writable directory for checkpoints"""
        candidates = [
            Path.cwd() / "checkpoints",  # Current directory (preferred)
            Path.home() / ".lung_nodule" / "checkpoints",  # User home
            Path(tempfile.gettempdir()) / "lung_nodule_checkpoints",  # Temp
        ]
        
        for candidate in candidates:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                # Test write permission
                test_file = candidate / ".write_test"
                test_file.touch()
                test_file.unlink()
                return candidate
            except (PermissionError, OSError):
                continue
        
        # Last resort: use temp directory without testing
        return Path(tempfile.gettempdir()) / "lung_nodule_checkpoints"
    
    def _ensure_directory(self):
        """Ensure checkpoint directory exists and is writable"""
        try:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠ Warning: Could not create checkpoint directory: {e}")
            print(f"   Checkpoints will not be saved.")
            self.checkpoint_dir = None
```

**Key Changes**:
- Try multiple directory locations in order of preference
- Test write permissions before using a directory
- Graceful degradation if no writable location found
- Clear warning messages to user

### 4. VC++ Runtime Installation Enhancement

#### main.py - VC++ Installation Logic

**Current Issues**:
- Silent failures with minimal feedback
- No user guidance on manual installation
- Runs on every startup if installation fails

**Design Solution**:

```python
def install_vcredist():
    """Install VC++ runtime with improved error handling"""
    bundle = Path(__file__).parent
    flag = bundle / '_vcredist' / '.done'
    vc = bundle / '_vcredist' / 'vc_redist.x64.exe'
    
    # Already installed
    if flag.exists():
        return True
    
    # Installer not found
    if not vc.exists():
        print("⚠ VC++ 运行库安装程序未找到")
        print(f"   请下载并放置到: {vc}")
        print("   下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        print("   或手动安装后程序将自动检测")
        return False
    
    # Attempt installation
    print("正在安装 Microsoft Visual C++ 运行库...")
    try:
        result = subprocess.run(
            [str(vc), '/quiet', '/norestart'],
            capture_output=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            flag.parent.mkdir(parents=True, exist_ok=True)
            flag.touch()
            print("✓ VC++ 运行库安装成功")
            return True
        else:
            print(f"⚠ VC++ 运行库安装失败 (错误码: {result.returncode})")
            print("   可能需要管理员权限，请尝试：")
            print(f"   1. 右键点击程序，选择'以管理员身份运行'")
            print(f"   2. 或手动运行: {vc}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠ VC++ 运行库安装超时")
        print("   请手动安装后重试")
        return False
    except Exception as e:
        print(f"⚠ VC++ 运行库安装失败: {e}")
        print(f"   请手动运行: {vc}")
        return False

# Call at startup
install_vcredist()
```

**Key Changes**:
- Detailed status messages at each step
- Specific error codes and troubleshooting guidance
- Timeout protection
- Download link provided when installer missing
- Returns boolean for success/failure tracking

### 5. Path Validation System

#### config_loader.py - Enhanced Validation

**Current Issues**:
- No validation of paths after loading
- Cryptic errors when files missing
- No guidance for users

**Design Solution**:

```python
def validate_config(config: Any) -> list[str]:
    """Validate configuration and return list of issues"""
    issues = []
    
    # Check base path
    base_path = getattr(config, '_ROOT', None)
    if base_path and not Path(base_path).exists():
        issues.append(f"Base path does not exist: {base_path}")
    
    # Check input file
    excel_path = getattr(config, 'EXCEL_PATH', None)
    if excel_path and not Path(excel_path).exists():
        issues.append(
            f"Input file not found: {excel_path}\n"
            f"   Please create or specify a valid Excel file"
        )
    
    # Check model paths
    model_paths = getattr(config, 'MODEL_PATHS', [])
    if not model_paths:
        issues.append("No model paths configured")
    else:
        for model_path in model_paths:
            if not Path(model_path).exists():
                issues.append(
                    f"Model file not found: {model_path}\n"
                    f"   Please download models to the 'models/' directory"
                )
    
    # Check models directory
    if base_path:
        models_dir = Path(base_path) / 'models'
        if not models_dir.exists():
            issues.append(
                f"Models directory not found: {models_dir}\n"
                f"   Please create the directory and add model files"
            )
    
    return issues

def load_config() -> Any:
    """Load and validate configuration"""
    # ... existing loading logic ...
    
    # Validate after loading
    issues = validate_config(default_config)
    if issues:
        print("\n⚠ Configuration Issues Detected:")
        for issue in issues:
            print(f"   • {issue}")
        print()
    
    return default_config
```

**Key Changes**:
- Validate all critical paths after loading
- Provide specific, actionable error messages
- Check for common missing directories
- Non-blocking warnings (doesn't prevent startup)

### 6. Build Script Improvements

#### build_gui.bat

**Current Issues**:
- Limited error checking
- No verification of prerequisites
- Silent failures on file operations

**Design Solution**:

```batch
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 打包前检查
echo ========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ PyInstaller 未安装
    echo    请运行: pip install pyinstaller
    pause
    exit /b 1
)

REM Check spec file
if not exist "gui.spec" (
    echo ❌ gui.spec 文件不存在
    pause
    exit /b 1
)

echo ✓ 环境检查通过
echo.

echo ========================================
echo 开始打包 GUI 版本
echo ========================================
echo.

echo [1/4] 清理旧的构建文件...
if exist "dist\医疗影像报告预测工具" (
    rmdir /s /q "dist\医疗影像报告预测工具"
    if errorlevel 1 (
        echo ⚠ 警告: 无法删除旧的 dist 目录，可能被占用
    )
)
if exist "build" (
    rmdir /s /q "build"
)
echo ✓ 完成
echo.

echo [2/4] 使用 PyInstaller 打包...
pyinstaller gui.spec --clean
if errorlevel 1 (
    echo.
    echo ❌ 打包失败！请检查上方错误信息
    pause
    exit /b 1
)
echo ✓ 完成
echo.

echo [3/4] 验证输出文件...
if not exist "dist\医疗影像报告预测工具\医疗影像报告预测工具.exe" (
    echo ❌ 可执行文件未生成
    pause
    exit /b 1
)
echo ✓ 可执行文件已生成
echo.

echo [4/4] 复制必要文件到发布目录...
if not exist "dist\医疗影像报告预测工具\models" mkdir "dist\医疗影像报告预测工具\models"
if not exist "dist\医疗影像报告预测工具\_vcredist" mkdir "dist\医疗影像报告预测工具\_vcredist"

REM 复制示例文件
if exist "test.xlsx" (
    copy "test.xlsx" "dist\医疗影像报告预测工具\" >nul
    echo ✓ 已复制示例文件
) else (
    echo ⚠ 未找到 test.xlsx
)

if exist "config.py" (
    copy "config.py" "dist\医疗影像报告预测工具\config_example.py" >nul
    echo ✓ 已复制配置示例
)

REM 复制VC++运行库
if exist "_vcredist\vc_redist.x64.exe" (
    copy "_vcredist\vc_redist.x64.exe" "dist\医疗影像报告预测工具\_vcredist\" >nul
    echo ✓ 已复制 VC++ 运行库
) else (
    echo ⚠ 未找到 VC++ 运行库
    echo    下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo    放置到: _vcredist\vc_redist.x64.exe
)

REM 复制模型文件
set MODEL_COUNT=0
for %%f in (models\*.gguf) do (
    copy "%%f" "dist\医疗影像报告预测工具\models\" >nul 2>&1
    if not errorlevel 1 set /a MODEL_COUNT+=1
)

if !MODEL_COUNT! gtr 0 (
    echo ✓ 已复制 !MODEL_COUNT! 个模型文件
) else (
    echo ⚠ 未找到模型文件
    echo    请将 .gguf 模型文件放置到 models\ 目录
)

echo ✓ 完成
echo.

echo ========================================
echo ✓ 打包完成！
echo ========================================
echo.
echo 发布目录: dist\医疗影像报告预测工具\
echo.
echo 📋 部署检查清单:
if !MODEL_COUNT! equ 0 echo    [ ] 复制模型文件到 models\ 目录
if not exist "_vcredist\vc_redist.x64.exe" echo    [ ] 复制 VC++ 运行库到 _vcredist\ 目录
echo    [ ] 测试运行可执行文件
echo    [ ] 压缩为 ZIP 或创建安装包
echo.
pause
```

**Key Changes**:
- Pre-flight checks for Python and PyInstaller
- Verify output file was created
- Count and report copied files
- Provide deployment checklist
- Better error messages with actionable guidance

### 7. Installer Configuration Updates

#### installer.iss

**Current Issues**:
- Example GUID (not unique)
- No version management
- Incomplete uninstall cleanup

**Design Solution**:

```iss
; Generate unique GUID: https://www.guidgenerator.com/
#define MyAppName "医疗影像报告预测工具"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Your Organization"
#define MyAppExeName "医疗影像报告预测工具.exe"
#define MyAppId "{{YOUR-UNIQUE-GUID-HERE}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename={#MyAppName}_v{#MyAppVersion}_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Handle Unicode properly
LanguageDetectionMethod=uilanguage

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppName}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Ensure models are in dist before building installer

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ runtime
Filename: "{app}\_vcredist\vc_redist.x64.exe"; Parameters: "/quiet /norestart"; StatusMsg: "正在安装 Microsoft Visual C++ 运行库..."; Flags: waituntilterminated skipifdoesntexist; Check: VCRedistNeedsInstall

; Launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up generated files
Type: filesandordirs; Name: "{app}\checkpoints"
Type: files; Name: "{app}\*.xlsx"
; Preserve user config
; Type: files; Name: "{app}\config.py"

[Code]
function VCRedistNeedsInstall: Boolean;
begin
  // Simple check - always try to install if present
  Result := FileExists(ExpandConstant('{app}\_vcredist\vc_redist.x64.exe'));
end;
```

**Key Changes**:
- Placeholder for unique GUID with generation link
- Version variable for easy updates
- Unicode language detection
- Conditional VC++ installation
- Preserve user config.py on uninstall
- Better file naming with version

## Data Models

### Configuration Schema

```python
@dataclass
class PackagingConfig:
    """Configuration for packaging system"""
    spec_root: Path
    hook_path: Path
    hidden_imports: list[str]
    data_files: list[tuple[str, str]]
    binaries: list[tuple[str, str]]

@dataclass
class RuntimeConfig:
    """Runtime configuration with validation"""
    base_path: Path
    excel_path: Path
    output_path: Path
    model_paths: list[Path]
    checkpoint_dir: Path
    
    def validate(self) -> list[str]:
        """Return list of validation errors"""
        ...
```

## Error Handling

### Error Categories and Responses

| Error Category | Detection | Response | User Guidance |
|---------------|-----------|----------|---------------|
| Missing Dependencies | Import failure | Log warning, continue | Install instructions |
| Path Not Found | File/dir check | Clear error message | Expected location |
| Permission Denied | Write test | Try fallback location | Admin instructions |
| Build Failure | Return code | Show full error | Check prerequisites |
| VC++ Install Fail | Return code | Manual install guide | Download link |

### Error Message Format

```python
def format_error(category: str, details: str, solution: str) -> str:
    return f"""
❌ {category}
   
   问题: {details}
   
   解决方案:
   {solution}
"""
```

## Testing Strategy

### Unit Tests

1. **Path Resolution Tests**
   - Test relative path resolution in different environments
   - Test SPECPATH variable usage
   - Test fallback mechanisms

2. **Checkpoint Manager Tests**
   - Test directory creation in various permission scenarios
   - Test fallback directory selection
   - Test graceful degradation

3. **Config Validation Tests**
   - Test validation with missing files
   - Test validation with invalid paths
   - Test error message formatting

### Integration Tests

1. **Build System Tests**
   - Test spec file processing on clean machine
   - Test hook file data collection
   - Test output verification

2. **Runtime Tests**
   - Test packaged app startup
   - Test config loading from external file
   - Test checkpoint save/load in restricted environment

### Manual Testing Checklist

- [ ] Build on machine without hardcoded paths
- [ ] Run packaged app without models directory
- [ ] Run packaged app in read-only directory
- [ ] Test VC++ installation with/without admin rights
- [ ] Test with Chinese characters in paths
- [ ] Test checkpoint resume after interruption
- [ ] Test external config.py override

## Documentation Updates

### README.md Structure

Add new section after "打包部署":

```markdown
## 打包问题修复指南

### 已修复的问题

1. **硬编码路径问题** - spec文件现在使用相对路径
2. **依赖缺失** - 补充了所有隐式导入
3. **权限问题** - 检查点目录自动选择可写位置
4. **VC++安装** - 改进错误提示和手动安装指导
5. **路径验证** - 启动时检查关键文件并提供清晰错误信息

### 常见打包错误

**错误: ModuleNotFoundError in packaged app**
- 原因: 隐式导入未声明
- 解决: 检查 spec 文件的 hiddenimports 列表

**错误: FileNotFoundError for data files**
- 原因: 数据文件未包含在打包中
- 解决: 检查 spec 文件的 datas 列表和 hook 文件

**错误: Permission denied for checkpoints**
- 原因: 程序在只读目录运行
- 解决: 程序会自动使用用户目录或临时目录

### 开发者注意事项

- 修改 spec 文件时使用 `SPECPATH` 变量
- 添加新依赖时更新 hiddenimports
- 测试打包后的程序在不同权限环境下运行
```

## Implementation Notes

### Phase 1: Critical Fixes (Priority 1)
- Fix hardcoded paths in main.spec
- Unify hiddenimports in both spec files
- Update hook file to collect all data

### Phase 2: Robustness (Priority 2)
- Implement safe checkpoint directory selection
- Enhance VC++ installation feedback
- Add path validation

### Phase 3: Polish (Priority 3)
- Update build script with checks
- Update installer configuration
- Add comprehensive documentation to README

### Backward Compatibility

- Existing config.py files will continue to work
- Old checkpoint files remain compatible
- No breaking changes to command-line interface
- GUI interface unchanged

### Performance Impact

- Minimal: Path validation adds <100ms to startup
- Checkpoint directory selection adds <50ms
- No impact on inference performance

## Conclusion

This design provides a comprehensive solution to all identified packaging issues while maintaining simplicity and backward compatibility. The fixes are integrated into existing files rather than creating new components, and all documentation is consolidated in README.md as requested.

The solution prioritizes developer experience (portable builds) and user experience (clear error messages) while maintaining the existing architecture and functionality of the application.
