# Requirements Document

## Introduction

This specification addresses critical packaging issues in the medical imaging report prediction tool that prevent successful builds on different machines and may cause runtime failures in packaged applications. The fixes will ensure the PyInstaller-based packaging system works reliably across different development environments and that the packaged application runs correctly with all dependencies.

**Note**: The detailed fix documentation will be integrated into the project's README.md file under a "Packaging Issues & Fixes" section, rather than creating separate documentation files.

## Glossary

- **Packaging System**: The PyInstaller-based build system that converts Python applications into standalone executables
- **Spec File**: PyInstaller specification file (.spec) that defines how the application should be packaged
- **Hidden Imports**: Python modules that PyInstaller cannot automatically detect and must be explicitly declared
- **Hook File**: PyInstaller hook script that collects additional data files and binaries for specific packages
- **Base Path**: The root directory path that differs between development and packaged environments
- **Checkpoint Directory**: The directory where the application saves progress checkpoints during batch processing
- **VC++ Runtime**: Microsoft Visual C++ Redistributable required by llama-cpp-python

## Requirements

### Requirement 1: Remove Hardcoded Paths

**User Story:** As a developer, I want to build the application on any machine without modifying spec files, so that the build process is portable and maintainable.

#### Acceptance Criteria

1. WHEN the build system processes main.spec, THE Packaging System SHALL use relative paths for all hook files and data files
2. WHEN the build system processes gui.spec, THE Packaging System SHALL use relative paths for all hook files and data files
3. WHEN a developer runs the build on a different machine, THE Packaging System SHALL locate all required files without path errors
4. WHEN the spec files reference project files, THE Packaging System SHALL resolve paths relative to the spec file location
5. WHERE the hook file is referenced, THE Packaging System SHALL use dynamic path resolution based on the current working directory

### Requirement 2: Standardize Dependency Configuration

**User Story:** As a developer, I want consistent dependency declarations across all spec files, so that both GUI and CLI versions include all required modules.

#### Acceptance Criteria

1. WHEN the build system processes any spec file, THE Packaging System SHALL include all Python standard library modules used by the application
2. WHEN the build system processes any spec file, THE Packaging System SHALL include all third-party package dependencies
3. WHEN the application uses pickle module, THE Packaging System SHALL include pickle in hiddenimports
4. WHEN the application uses concurrent.futures module, THE Packaging System SHALL include concurrent.futures in hiddenimports
5. WHEN the application uses importlib.util module, THE Packaging System SHALL include importlib.util in hiddenimports
6. WHERE both gui.spec and main.spec exist, THE Packaging System SHALL declare identical core dependencies in both files

### Requirement 3: Complete Data File Collection

**User Story:** As a developer, I want all necessary data files automatically included in the package, so that the application has access to required resources at runtime.

#### Acceptance Criteria

1. WHEN the hook file collects pandas data, THE Packaging System SHALL include all pandas data files not just the core subdirectory
2. WHEN the hook file processes openpyxl, THE Packaging System SHALL collect openpyxl data files and metadata
3. WHEN the build system packages the application, THE Packaging System SHALL include config.py as a data file
4. WHEN the spec file declares data files, THE Packaging System SHALL use relative paths for all data file sources
5. WHERE the application requires example files, THE Packaging System SHALL document the manual file placement requirements

### Requirement 4: Improve Hook File Completeness

**User Story:** As a developer, I want the PyInstaller hook to collect all necessary package data, so that packaged applications do not fail due to missing resources.

#### Acceptance Criteria

1. WHEN the hook collects llama_cpp binaries, THE Packaging System SHALL include all dynamic libraries for llama_cpp
2. WHEN the hook collects pandas data, THE Packaging System SHALL include all pandas data files without subdirectory restrictions
3. WHEN the hook collects openpyxl data, THE Packaging System SHALL include openpyxl data files and dependencies
4. WHEN the hook collects tqdm data, THE Packaging System SHALL include tqdm data files
5. WHERE package data collection fails, THE Packaging System SHALL log warnings without stopping the build

### Requirement 5: Handle Checkpoint Directory Safely

**User Story:** As an end user, I want the application to save checkpoints without permission errors, so that I can resume interrupted processing tasks.

#### Acceptance Criteria

1. WHEN the application initializes CheckpointManager without arguments, THE Application SHALL create the checkpoint directory in a user-writable location
2. WHEN the application runs in a restricted permissions environment, THE Application SHALL fall back to the user's temporary directory for checkpoints
3. WHEN the checkpoint directory creation fails, THE Application SHALL display a clear error message to the user
4. WHEN the application attempts to save a checkpoint, THE Application SHALL verify write permissions before attempting the save operation
5. WHERE the application runs from a read-only location, THE Application SHALL use an alternative writable directory for checkpoints

### Requirement 6: Enhance VC++ Runtime Installation

**User Story:** As an end user, I want clear feedback about VC++ runtime installation, so that I understand what is happening and can troubleshoot issues.

#### Acceptance Criteria

1. WHEN the application detects missing VC++ runtime, THE Application SHALL display a user-friendly message explaining the requirement
2. WHEN the VC++ installer runs, THE Application SHALL show installation progress or status
3. IF the VC++ installation fails due to permissions, THEN THE Application SHALL provide instructions for manual installation
4. WHEN the VC++ installation completes successfully, THE Application SHALL create a marker file to prevent repeated installations
5. WHERE the VC++ installer is missing, THE Application SHALL provide a download link and continue without failing

### Requirement 7: Validate Packaged Application Paths

**User Story:** As an end user, I want helpful error messages when required files are missing, so that I can resolve configuration issues quickly.

#### Acceptance Criteria

1. WHEN the application loads configuration, THE Application SHALL verify that the base path is accessible
2. WHEN the application references model files, THE Application SHALL check if the models directory exists
3. IF required files are missing, THEN THE Application SHALL display specific error messages indicating which files are missing
4. WHEN the application starts, THE Application SHALL validate critical paths before attempting operations
5. WHERE configuration files are missing, THE Application SHALL provide instructions for creating them from examples

### Requirement 8: Update Installer Configuration

**User Story:** As a developer, I want the installer to have proper configuration, so that users can install and uninstall the application cleanly.

#### Acceptance Criteria

1. WHEN the installer is built, THE Installer System SHALL use a unique GUID for the application ID
2. WHEN the installer runs, THE Installer System SHALL handle Chinese characters in paths correctly
3. WHEN the user uninstalls the application, THE Installer System SHALL preserve user-created configuration files
4. WHEN the user uninstalls the application, THE Installer System SHALL remove generated checkpoint files
5. WHERE the installer includes VC++ runtime, THE Installer System SHALL handle installation failures gracefully

### Requirement 9: Improve Build Script Robustness

**User Story:** As a developer, I want the build script to handle errors gracefully, so that I can identify and fix build issues quickly.

#### Acceptance Criteria

1. WHEN the build script runs, THE Build System SHALL verify that required tools are installed before starting
2. WHEN PyInstaller encounters errors, THE Build System SHALL display the error details clearly
3. WHEN file copying operations fail, THE Build System SHALL report which files could not be copied
4. WHEN the build completes, THE Build System SHALL verify that the output executable was created
5. WHERE optional files are missing, THE Build System SHALL warn but continue the build process

### Requirement 10: Add Path Encoding Safety

**User Story:** As a developer, I want the build system to handle Chinese characters safely, so that the application works on all Windows systems.

#### Acceptance Criteria

1. WHEN the spec file defines the executable name, THE Packaging System SHALL properly encode Chinese characters
2. WHEN the build script processes paths, THE Build System SHALL use UTF-8 encoding consistently
3. WHEN the application creates files, THE Application SHALL handle Chinese characters in filenames safely
4. WHEN the installer creates shortcuts, THE Installer System SHALL properly encode Chinese application names
5. WHERE file operations involve Chinese characters, THE Application SHALL validate encoding compatibility
