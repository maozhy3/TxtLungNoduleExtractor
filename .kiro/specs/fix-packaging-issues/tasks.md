# Implementation Plan

- [ ] 1. Fix spec files with dynamic path resolution
  - Update main.spec to use SPECPATH for relative paths
  - Update gui.spec to use SPECPATH for relative paths
  - Unify hiddenimports list across both spec files
  - Add config.py to datas in both spec files
  - Remove all hardcoded absolute paths
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.4_

- [ ] 2. Enhance hook file for complete data collection
  - Remove subdir='core' restriction from pandas collection
  - Add openpyxl data collection
  - Wrap each collection in try-except blocks
  - Add warning messages for collection failures
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. Implement safe checkpoint directory handling
  - [ ] 3.1 Add _get_safe_checkpoint_dir method to CheckpointManager
    - Implement directory candidate list (cwd, home, temp)
    - Add write permission testing for each candidate
    - Return first writable directory
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [ ] 3.2 Add _ensure_directory method to CheckpointManager
    - Create directory with error handling
    - Set checkpoint_dir to None on failure
    - Display warning message to user
    - _Requirements: 5.3, 5.4_
  
  - [ ] 3.3 Update CheckpointManager.__init__
    - Call _get_safe_checkpoint_dir when checkpoint_dir is None
    - Call _ensure_directory after setting checkpoint_dir
    - _Requirements: 5.1, 5.2_

- [ ] 4. Enhance VC++ runtime installation
  - [ ] 4.1 Create install_vcredist function in main.py
    - Check if already installed (flag file exists)
    - Check if installer file exists
    - Display download link if installer missing
    - _Requirements: 6.1, 6.5_
  
  - [ ] 4.2 Implement installation with detailed feedback
    - Add status message before installation
    - Use subprocess.run with capture_output and timeout
    - Check return code and display success/failure
    - Provide troubleshooting guidance on failure
    - _Requirements: 6.2, 6.3, 6.4_
  
  - [ ] 4.3 Update main.py startup to call install_vcredist
    - Replace existing VC++ installation code
    - Call install_vcredist() before main logic
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 5. Add configuration path validation
  - [ ] 5.1 Create validate_config function in config_loader.py
    - Check base path exists
    - Check input file exists with helpful message
    - Check model paths exist with helpful message
    - Check models directory exists with helpful message
    - Return list of issue strings
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 5.2 Update load_config to call validation
    - Call validate_config after loading configuration
    - Display warning messages for any issues found
    - Continue execution (non-blocking warnings)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 6. Improve build script robustness
  - [ ] 6.1 Add pre-flight checks to build_gui.bat
    - Check Python is installed and in PATH
    - Check PyInstaller is installed
    - Check gui.spec file exists
    - Display error and exit if checks fail
    - _Requirements: 9.1, 9.5_
  
  - [ ] 6.2 Add output verification to build_gui.bat
    - Check if executable file was created
    - Display error if output missing
    - _Requirements: 9.4_
  
  - [ ] 6.3 Enhance file copying with feedback
    - Count copied model files
    - Report status for each file type
    - Provide deployment checklist at end
    - _Requirements: 9.3, 9.5_
  
  - [ ] 6.4 Improve error messages in build_gui.bat
    - Add specific error messages for each failure point
    - Include actionable guidance in error messages
    - _Requirements: 9.2, 9.3_

- [ ] 7. Update installer configuration
  - Add comment with GUID generator link
  - Update version variable to 1.1.0
  - Add LanguageDetectionMethod for Unicode handling
  - Add VCRedistNeedsInstall function
  - Update OutputBaseFilename to include version
  - Comment out config.py deletion in UninstallDelete
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 10.1, 10.2, 10.4_

- [ ] 8. Update README.md with packaging fixes documentation
  - [ ]* 8.1 Add "打包问题修复指南" section after "打包部署"
    - List all 10 fixed issues with brief descriptions
    - _Requirements: All requirements (documentation)_
  
  - [ ]* 8.2 Add "常见打包错误" subsection
    - Document ModuleNotFoundError solution
    - Document FileNotFoundError solution
    - Document Permission denied solution
    - _Requirements: 2.1-2.6, 3.1-3.5, 5.1-5.5_
  
  - [ ]* 8.3 Add "开发者注意事项" subsection
    - Document SPECPATH usage
    - Document hiddenimports maintenance
    - Document testing in different environments
    - _Requirements: 1.1-1.5, 2.1-2.6_

- [ ] 9. Verify all changes work together
  - [ ]* 9.1 Test build on clean machine
    - Clone repository to new location
    - Run build_gui.bat
    - Verify no hardcoded path errors
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 9.2 Test packaged application
    - Run executable in different directories
    - Test with missing models directory
    - Test checkpoint creation in read-only location
    - Verify error messages are clear and helpful
    - _Requirements: 5.1-5.5, 7.1-7.5_
  
  - [ ]* 9.3 Test configuration override
    - Create external config.py next to executable
    - Verify external config is loaded
    - Verify validation messages appear
    - _Requirements: 7.1-7.5_
