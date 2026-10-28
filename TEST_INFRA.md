# Test Infrastructure: Yunmai Massage Gun Pro (YMFG-B563) Reverse Engineering Repository

This document specifies the end-to-end (E2E) test architecture, verification methodology, test tier definitions, and invocation instructions for validating the `yunmai-massage-gun-pro-reverse-engineering` repository.

---

## 1. Architecture & Design Principles

The test suite implements an **opaque-box verification architecture** designed to ensure the repository meets the highest engineering standards for public hardware reverse-engineering documentation.

### Core Architectural Principles
1. **Opaque-Box Testing**: Tests inspect observable repository outputs, physical filesystem layouts, git object trees, binary magic headers, and CLI tool interfaces without coupling to internal generation mechanisms.
2. **Progressive Testability**: Each test maps to specific milestone deliverables (M1: Asset Reorganization, M2: Documentation Suite, M3: GitHub Publication, M4: Final Verification). Tests fail clearly with actionable messages when a milestone deliverable is pending, and pass cleanly when implemented.
3. **True Case-Sensitivity**: Because Windows NTFS lookups are case-insensitive by default while GitHub/Linux environments are case-sensitive, the test suite implements entry-by-entry directory enumeration to catch capitalization mismatches that would cause 404 errors on GitHub.
4. **Binary & Media Integrity**: Image and PDF assets are verified not only for physical file presence and non-zero size, but also against magic byte headers (`\xFF\xD8\xFF` for JPEG, `\x89PNG` for PNG, `%PDF-` for PDF) to detect corrupted or stub files.
5. **Zero Workspace Side-Effects**: All tests operate in read-only mode and produce zero temporary artifacts, cache files, or git modifications.
6. **Zero External Dependencies**: Built entirely upon Python's standard library (`unittest`, `pathlib`, `subprocess`, `re`, `json`, `os`, `sys`, `time`). No virtual environment or `pip install` required.

---

## 2. 4-Tier Test Matrix

The suite contains **17 automated tests** structured across 4 hierarchical tiers:

```
tests/test_e2e.py
├── Tier 1: Feature Coverage (8 tests)
│   ├── test_01_directory_structure
│   ├── test_02_asset_presence_and_integrity
│   ├── test_03_gitignore_exclusions
│   ├── test_04_readme_presence_and_documentation
│   ├── test_05_arduino_test_sketch_configuration
│   ├── test_06_git_remote_configured
│   ├── test_07_license_file
│   └── test_08_supporting_docs_present
├── Tier 2: Boundary & Corner Cases (4 tests)
│   ├── test_01_git_history_no_blobs_exceeding_100mb
│   ├── test_02_all_markdown_links_resolve_without_broken_paths
│   ├── test_03_case_sensitivity_for_cross_platform_compatibility
│   └── test_04_exclusion_of_os_and_temporary_artifacts
├── Tier 3: Cross-Feature Interactions (3 tests)
│   ├── test_01_readme_image_embeds_match_physical_files
│   ├── test_02_pinout_specs_match_datasheet
│   └── test_03_git_remote_matches_gh_repo_view
└── Tier 4: Real-World Scenarios (2 tests)
    ├── test_01_cli_runner_execution_and_clean_workspace
    └── test_02_e2e_release_readiness_scenario
```

### Detailed Tier Specifications

#### Tier 1: Feature Coverage
- **`test_01_directory_structure`**: Verifies that all 15 semantic directories exist (`docs/manuals`, `hardware/datasheets`, `hardware/photos/hero`, `hardware/photos/teardown`, `hardware/photos/pcb`, `hardware/photos/ui`, `hardware/photos/battery`, `hardware/photos/charger`, `firmware/arduino/massage_gun_test`, `notes`).
- **`test_02_asset_presence_and_integrity`**: Verifies presence, non-zero file size, and binary magic bytes for all 36 relocated workspace assets (2 PDF manuals, 2 datasheets/diagrams, 29 photography assets, 1 Arduino sketch, 2 diagnostic notes).
- **`test_03_gitignore_exclusions`**: Confirms root `.gitignore` exists and excludes OS artifacts (`desktop.ini`, `Thumbs.db`), agent metadata (`.agents/`), and binary installers (`*.exe`).
- **`test_04_readme_presence_and_documentation`**: Validates root `README.md` exists (>2000 characters) and contains core technical sections: Model `YMFG-B563`, mainboard `YM-B563-MAIN-V0.3`, motor `2430BL`, 25 kHz PWM frequency, 21.6V battery, 26V charger, reverse-polarity wire color hazard warning, and Arduino Timer1 test harness.
- **`test_05_arduino_test_sketch_configuration`**: Asserts that `firmware/arduino/massage_gun_test/massage_gun_test.ino` configures hardware Timer1 Fast PWM (`ICR1 = 639` for ~25 kHz), sets pins `PIN_PWM=9`, `PIN_DIR=8`, `PIN_FG=2`, and properly handles active-LOW inverted motor drive logic.
- **`test_06_git_remote_configured`**: Verifies local git remote `origin` is set to `yunmai-massage-gun-pro-reverse-engineering`.
- **`test_07_license_file`**: Asserts root `LICENSE` exists and grants open MIT documentation license.
- **`test_08_supporting_docs_present`**: Confirms supporting engineering guides in `docs/` (`hardware-analysis.md`, `pinouts-and-signals.md`, `mechanical-teardown.md`) exist.

#### Tier 2: Boundary & Corner Cases
- **`test_01_git_history_no_blobs_exceeding_100mb`**: Performs a full git object database inspection (`git cat-file --batch-check ... --batch-all-objects`) to guarantee that NO object in git history exceeds GitHub's 100 MB hard limit (`GH001`). Specifically guards against `arduino-ide_2.3.7_Windows_64bit.exe` (150.67 MB).
- **`test_02_all_markdown_links_resolve_without_broken_paths`**: Crawls all markdown files across the repository, extracts every local relative link (`[text](path)`, `![alt](path)`, `<img src="path">`), and asserts that every target file exists on disk.
- **`test_03_case_sensitivity_for_cross_platform_compatibility`**: Performs entry-by-entry directory checks for all assets and markdown links to prevent Linux/GitHub Pages 404 errors caused by Windows filesystem case-insensitivity.
- **`test_04_exclusion_of_os_and_temporary_artifacts`**: Inspects `git ls-files` to ensure no `desktop.ini`, `Thumbs.db`, `.DS_Store`, `*.exe`, `reverse-engineering/v1/`, `reverse-engineering/v2/`, or `Blink.txt` stubs are tracked.

#### Tier 3: Cross-Feature Interactions
- **`test_01_readme_image_embeds_match_physical_files`**: Validates that all images embedded in `README.md` physically exist on disk, have valid JPEG/PNG headers, and provide visual coverage across all 7 hardware subsystems (hero, PCB, teardown, battery, charger, UI, datasheet).
- **`test_02_pinout_specs_match_datasheet`**: Validates cross-consistency between documentation, Arduino firmware, and Dongguan E-S Motor 2430BL datasheet:
  - CN2 connector: Pin 1 = 26V Vm (Red), Pin 2 = FG 6 pulses/rev (White/Green), Pin 3 = FR (Yellow), Pin 4 = GND (Black), Pin 5 = PWM active-low (Blue).
  - Hazard warning: Explicit alert that UI PCB pad `GND` connects to a RED wire and pad `KEY` connects to a BLACK wire.
  - Arduino Timer1 frequency (25 kHz) matches motor driver requirements (15-25 kHz).
- **`test_03_git_remote_matches_gh_repo_view`**: Validates git remote configuration against `gh repo view` to confirm the public repository exists under account `olekkut`.

#### Tier 4: Real-World Scenarios
- **`test_01_cli_runner_execution_and_clean_workspace`**: Executes the test runner CLI directly via subprocess, confirms clean exit code and formatted output, and asserts zero workspace pollution.
- **`test_02_e2e_release_readiness_scenario`**: Simulates an external engineer cloning the repository, asserting complete availability of LICENSE, README, PDF user manuals, and curated teardown photography.

---

## 3. Invocation Commands

The test suite can be run with Python directly or via Python's standard `unittest` framework:

### Complete Suite Execution
```powershell
python tests/test_e2e.py
```

### Tier-Specific Execution
```powershell
# Run Tier 1 only (Feature Coverage)
python tests/test_e2e.py --tier 1

# Run Tier 2 only (Boundary & Corner Cases)
python tests/test_e2e.py --tier 2

# Run Tier 3 only (Cross-Feature Interactions)
python tests/test_e2e.py --tier 3

# Run Tier 4 only (Real-World Scenarios)
python tests/test_e2e.py --tier 4
```

### Standard Unittest Invocation
```powershell
# Run via unittest module
python -m unittest tests/test_e2e.py

# Run via unittest discovery
python -m unittest discover tests -v
```

---

## 4. Milestone Verification Mapping

| Milestone | Scope | Associated Test Cases | Expected Pass State |
|---|---|---|---|
| **M1** | Asset Reorganization & History Remediation | Tier 1 (tests 01, 02, 03, 05) + Tier 2 (tests 01, 02, 03, 04) | **PASS** (8/8 tests pass) |
| **M2** | Comprehensive Documentation Suite | Tier 1 (tests 04, 07, 08) + Tier 3 (tests 01, 02) + Tier 4 (test 02) | **PASS** (6/6 tests pass) |
| **M3** | GitHub Publication & Remote Setup | Tier 1 (test 06) + Tier 3 (test 03) | **PASS** (2/2 tests pass) |
| **M4** | Final E2E Audit & Quality Sign-Off | All 17 tests across Tiers 1-4 | **PASS** (17/17 tests pass, exit code 0) |

---

## 5. Test Maintenance Guidelines
- When adding new assets to the repository, add the relative path to `EXPECTED_ASSETS` in `tests/test_e2e.py`.
- Ensure all photography file extensions are lowercase (`.jpg` or `.png`).
- Never add dummy or facade tests; every test must perform real disk, git, or binary inspection.
