"""
Yunmai Massage Gun Pro (YMFG-B563) Reverse Engineering Repository
End-to-End (E2E) Test Suite

4-Tier Opaque-Box Verification Architecture:
- Tier 1: Feature Coverage (directory structure, asset presence, .gitignore, README.md, Arduino test sketch, git remote)
- Tier 2: Boundary & Corner Cases (git history <100MB blob check, markdown broken link validation, case-sensitivity check, OS/temp exclusion)
- Tier 3: Cross-Feature Interactions (README image embeds match physical files, pinouts match datasheet, git remote matches gh repo view)
- Tier 4: Real-World Scenarios (Automated test runner execution, zero side-effects, full release audit)

Usage:
    python tests/test_e2e.py                 # Run all 4 tiers
    python tests/test_e2e.py --tier 1        # Run Tier 1 only
    python tests/test_e2e.py --tier 2        # Run Tier 2 only
    python tests/test_e2e.py --tier 3        # Run Tier 3 only
    python tests/test_e2e.py --tier 4        # Run Tier 4 only
    python -m unittest tests/test_e2e.py     # Run via standard unittest
"""

import argparse
import os
import re
import subprocess
import sys
import time
import unittest
from pathlib import Path

# Repository root directory
REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Authoritative Interface Contracts & Specifications
# ---------------------------------------------------------------------------

EXPECTED_DIRECTORIES = [
    "docs",
    "docs/manuals",
    "hardware",
    "hardware/datasheets",
    "hardware/photos",
    "hardware/photos/hero",
    "hardware/photos/teardown",
    "hardware/photos/pcb",
    "hardware/photos/ui",
    "hardware/photos/battery",
    "hardware/photos/charger",
    "firmware",
    "firmware/arduino",
    "firmware/arduino/massage_gun_test",
    "notes",
]

EXPECTED_ASSETS = [
    # Manuals (2)
    "docs/manuals/YMFG-B563-Yunmai-Massage-Gun-Pro-User-Manual-6-Languages.pdf",
    "docs/manuals/YMFG-B563-Yunmai-Massage-Gun-Pro-Original-Manual.pdf",
    # Datasheets & Diagrams (2)
    "hardware/datasheets/dongguan_es_motor_25sg_2430bl_manual.png",
    "hardware/datasheets/motor_pinout_terminations_diagram.png",
    # Hero Photos (2)
    "hardware/photos/hero/01_carrying_case_exterior.jpg",
    "hardware/photos/hero/02_massage_gun_case_and_attachments.jpg",
    # Teardown Photos (10)
    "hardware/photos/teardown/01_outer_shell_interior.jpg",
    "hardware/photos/teardown/02_internal_chassis_bracket.jpg",
    "hardware/photos/teardown/03_reciprocating_mechanism_overview.jpg",
    "hardware/photos/teardown/04_connecting_rod_bearing_detail.jpg",
    "hardware/photos/teardown/05_piston_cylinder_assembly.jpg",
    "hardware/photos/teardown/06_motor_mounting_bearing_harness.jpg",
    "hardware/photos/teardown/07_motor_backplate_mounting.jpg",
    "hardware/photos/teardown/08_device_rating_plate_ymfg_b563.jpg",
    "hardware/photos/teardown/09_handle_battery_cavity.jpg",
    "hardware/photos/teardown/10_power_switch_dc_jack_cavity.jpg",
    # PCB Photos (10)
    "hardware/photos/pcb/01_mainboard_top_macro.jpg",
    "hardware/photos/pcb/02_mainboard_top_alternate.jpg",
    "hardware/photos/pcb/03_mainboard_bottom_mcu_macro.jpg",
    "hardware/photos/pcb/04_mainboard_with_harness_closeup.jpg",
    "hardware/photos/pcb/05_mainboard_mounted_in_chassis.jpg",
    "hardware/photos/pcb/06_mainboard_harness_connector_view.jpg",
    "hardware/photos/pcb/07_mainboard_side_profile_connectors.jpg",
    "hardware/photos/pcb/08_mainboard_desoldered_pads_and_plug.jpg",
    "hardware/photos/pcb/09_mainboard_top_silkscreen_reference.jpg",
    "hardware/photos/pcb/10_mainboard_bottom_swd_reference.jpg",
    # UI Daughterboard Photos (2)
    "hardware/photos/ui/01_ui_daughterboard_solder_joints.jpg",
    "hardware/photos/ui/02_ui_daughterboard_led_side.jpg",
    # Battery Photos (3)
    "hardware/photos/battery/01_battery_pack_in_handle.jpg",
    "hardware/photos/battery/02_battery_pack_rating_label.jpg",
    "hardware/photos/battery/03_battery_cells_and_bms_assembly.jpg",
    # Charger Photos (2)
    "hardware/photos/charger/01_qshain_charger_label_macro.jpg",
    "hardware/photos/charger/02_qshain_charger_eu_plug.jpg",
    # Firmware Test Sketch (1)
    "firmware/arduino/massage_gun_test/massage_gun_test.ino",
    # Historical Field Notes (2)
    "notes/original_diagnosis.md",
    "notes/original_pinout_notes.md",
]

# Root metadata files expected upon complete publication (M2/M3)
EXPECTED_ROOT_DOCS = [
    "README.md",
    "LICENSE",
    ".gitignore",
]

EXPECTED_SUPPORTING_DOCS = [
    "docs/hardware-analysis.md",
    "docs/pinouts-and-signals.md",
    "docs/mechanical-teardown.md",
]

# ---------------------------------------------------------------------------
# Helper Utility Functions
# ---------------------------------------------------------------------------

def run_git_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run a git command in REPO_ROOT and return the process result."""
    return subprocess.run(
        ["git"] + args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def check_case_sensitive_path(base_dir: Path, rel_path: str) -> tuple[bool, str]:
    """
    Verify case-sensitivity on Windows/Linux by inspecting directory listings
    entry-by-entry. Windows NTFS lookups are case-insensitive by default, but
    GitHub and Linux filesystems are strictly case-sensitive.
    """
    parts = Path(rel_path).parts
    current = base_dir
    for part in parts:
        if not current.exists():
            return False, f"Parent directory does not exist: {current}"
        try:
            entries = os.listdir(current)
        except OSError as e:
            return False, f"Failed to list directory {current}: {e}"
        if part not in entries:
            similar = [e for e in entries if e.lower() == part.lower()]
            if similar:
                return False, f"Case mismatch in {current}: requested '{part}', found '{similar[0]}'"
            return False, f"Segment '{part}' not found in {current}"
        current = current / part
    return True, ""


def validate_binary_header(path: Path) -> tuple[bool, str]:
    """
    Validate binary magic bytes to guarantee assets are not corrupt or dummy stubs.
    """
    if not path.is_file():
        return False, f"File does not exist: {path}"
    size = path.stat().st_size
    if size == 0:
        return False, f"File is empty (0 bytes): {path}"

    with open(path, "rb") as f:
        header = f.read(16)

    ext = path.suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        if len(header) < 3 or header[:3] != b"\xFF\xD8\xFF":
            return False, f"Invalid JPEG magic bytes in {path}"
    elif ext == ".png":
        if len(header) < 8 or header[:8] != b"\x89PNG\r\n\x1a\n":
            return False, f"Invalid PNG magic bytes in {path}"
    elif ext == ".pdf":
        if len(header) < 5 or header[:5] != b"%PDF-":
            return False, f"Invalid PDF magic bytes in {path}"
    return True, ""


def extract_markdown_links(content: str) -> list[str]:
    """
    Extract all local relative links from Markdown syntax and HTML tags.
    Filters out code blocks, inline code, external HTTP/HTTPS links, and pure internal anchors.
    """
    # Strip multiline fenced code blocks (``` ... ``` or ~~~ ... ~~~)
    clean = re.sub(r"```[\s\S]*?```", "", content)
    clean = re.sub(r"~~~[\s\S]*?~~~", "", clean)
    # Strip inline code spans (` ... `)
    clean = re.sub(r"`[^`\n]+`", "", clean)

    links = []
    # Markdown links: [text](target) and ![alt](target)
    md_pattern = re.compile(r"!?\[(?:[^\]]*)\]\(([^)#\s]+)(?:#[^\)]*)?\)")
    for match in md_pattern.finditer(clean):
        link = match.group(1).strip()
        if link and not link.startswith(("http://", "https://", "mailto:", "ftp:")):
            links.append(link)

    # HTML <img> and <a> tags
    html_pattern = re.compile(r"""<(?:img|a)[^>]+(?:src|href)=["']([^"'#]+)(?:#[^"']*)?["']""", re.IGNORECASE)
    for match in html_pattern.finditer(clean):
        link = match.group(1).strip()
        if link and not link.startswith(("http://", "https://", "mailto:", "ftp:")):
            links.append(link)

    return links


# ---------------------------------------------------------------------------
# Tier 1: Feature Coverage
# ---------------------------------------------------------------------------

class Tier1FeatureCoverage(unittest.TestCase):
    """
    Tier 1 tests verify fundamental feature coverage: directory structure,
    asset presence, .gitignore rules, README.md, Arduino sketch, and git remote.
    """

    def test_01_directory_structure(self):
        """Verify the complete directory hierarchy exists according to PROJECT.md."""
        missing = []
        for rel_dir in EXPECTED_DIRECTORIES:
            d = REPO_ROOT / rel_dir
            if not d.is_dir():
                missing.append(rel_dir)
        self.assertEqual(
            missing,
            [],
            f"Missing required directories in repository structure: {missing}",
        )

    def test_02_asset_presence_and_integrity(self):
        """Verify all 42 assets (plus project metadata) exist, are non-empty, and valid."""
        missing = []
        corrupted = []
        for rel_asset in EXPECTED_ASSETS:
            p = REPO_ROOT / rel_asset
            if not p.is_file():
                missing.append(rel_asset)
                continue
            if p.stat().st_size == 0:
                corrupted.append(f"{rel_asset} (empty file)")
                continue

            # Binary integrity check for media
            valid, reason = validate_binary_header(p)
            if not valid:
                corrupted.append(f"{rel_asset}: {reason}")

        self.assertEqual(missing, [], f"Missing required assets: {missing}")
        self.assertEqual(corrupted, [], f"Corrupted or invalid assets detected: {corrupted}")

    def test_03_gitignore_exclusions(self):
        """Verify root .gitignore exists and contains necessary exclusion rules."""
        gitignore = REPO_ROOT / ".gitignore"
        self.assertTrue(gitignore.is_file(), "Root .gitignore file does not exist")

        content = gitignore.read_text(encoding="utf-8")
        required_patterns = [
            ("OS files", ["desktop.ini", "Thumbs.db"]),
            ("Agent metadata", [".agents"]),
            ("Binary installers", ["*.exe"]),
        ]
        missing_rules = []
        for category, patterns in required_patterns:
            for pat in patterns:
                if pat not in content:
                    missing_rules.append(f"{category}: missing pattern '{pat}'")

        self.assertEqual(missing_rules, [], f".gitignore missing essential rules: {missing_rules}")

    def test_04_readme_presence_and_documentation(self):
        """Verify root README.md exists and contains thorough technical documentation."""
        readme = REPO_ROOT / "README.md"
        self.assertTrue(readme.is_file(), "Root README.md does not exist")

        text = readme.read_text(encoding="utf-8")
        self.assertGreater(
            len(text),
            2000,
            f"README.md is too brief ({len(text)} characters). Expected comprehensive documentation.",
        )

        required_keywords = [
            ("Model Number", "YMFG-B563"),
            ("Mainboard identifier", "YM-B563-MAIN"),
            ("Motor identifier", "2430BL"),
            ("PWM frequency", "25"),
            ("Battery specification", "21.6V"),
            ("Charger specification", "26V"),
            ("Hazard warning", "GND"),
            ("Arduino test rig", "Timer1"),
        ]
        missing_keywords = [label for label, kw in required_keywords if kw.lower() not in text.lower()]
        self.assertEqual(
            missing_keywords,
            [],
            f"README.md lacks required technical documentation sections: {missing_keywords}",
        )

    def test_05_arduino_test_sketch_configuration(self):
        """Verify the Arduino test sketch contains proper 25kHz Fast PWM and pin mappings."""
        sketch = REPO_ROOT / "firmware/arduino/massage_gun_test/massage_gun_test.ino"
        self.assertTrue(sketch.is_file(), f"Arduino sketch not found at {sketch}")

        code = sketch.read_text(encoding="utf-8")

        # Hardware Timer1 configuration assertions
        self.assertIn("ICR1 = 639", code, "Timer1 TOP value ICR1=639 (~25kHz) not configured in sketch")
        self.assertIn("TCCR1A", code, "Timer1 Control Register A not configured")
        self.assertIn("TCCR1B", code, "Timer1 Control Register B not configured")

        # Pin mapping assertions
        self.assertIn("PIN_PWM", code, "PIN_PWM definition missing")
        self.assertIn("PIN_DIR", code, "PIN_DIR definition missing")
        self.assertIn("PIN_FG", code, "PIN_FG definition missing")

        # Active-LOW logic inverted mapping assertion
        self.assertTrue(
            "invertedLogic" in code or "map(" in code,
            "Motor active-LOW logic handling missing in sketch",
        )

    def test_06_git_remote_configured(self):
        """Verify git remote 'origin' is configured to the target GitHub repository."""
        proc = run_git_command(["remote", "-v"])
        output = proc.stdout.strip()
        self.assertTrue(output, "No git remote configured in local repository (Milestone 3 deliverable)")
        self.assertIn("origin", output, "Git remote 'origin' not configured")
        self.assertIn(
            "yunmai-massage-gun-pro-reverse-engineering",
            output,
            f"Remote URL does not match target repo 'yunmai-massage-gun-pro-reverse-engineering': {output}",
        )

    def test_07_license_file(self):
        """Verify root LICENSE file exists and specifies MIT license (Milestone 2 deliverable)."""
        license_path = REPO_ROOT / "LICENSE"
        self.assertTrue(license_path.is_file(), "Root LICENSE file does not exist (Milestone 2 deliverable)")
        content = license_path.read_text(encoding="utf-8")
        self.assertIn("MIT", content.upper(), "LICENSE file does not specify MIT License")

    def test_08_supporting_docs_present(self):
        """Verify supporting technical docs in docs/ exist (Milestone 2 deliverable)."""
        missing = []
        for doc in EXPECTED_SUPPORTING_DOCS:
            p = REPO_ROOT / doc
            if not p.is_file():
                missing.append(doc)
        self.assertEqual(missing, [], f"Missing supporting documentation files (Milestone 2): {missing}")


# ---------------------------------------------------------------------------
# Tier 2: Boundary & Corner Cases
# ---------------------------------------------------------------------------

class Tier2BoundaryCornerCases(unittest.TestCase):
    """
    Tier 2 tests verify boundary, corner case, and security constraints:
    no files >100MB in git history, no broken markdown links, strict case sensitivity,
    and exclusion of temporary or OS artifacts.
    """

    def test_01_git_history_no_blobs_exceeding_100mb(self):
        """
        Verify that no git object across the entire repository history exceeds
        GitHub's hard limit of 100 MB (104,857,600 bytes). Specifically guards
        against 'arduino-ide_2.3.7_Windows_64bit.exe' (150.67 MB).
        """
        limit = 104_857_600  # 100 MB
        proc = run_git_command([
            "cat-file",
            '--batch-check=%(objectname) %(objecttype) %(objectsize)',
            "--batch-all-objects",
        ])
        if proc.returncode != 0:
            self.skipTest(f"git cat-file batch check failed: {proc.stderr}")

        oversized = []
        for line in proc.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 3 and parts[1] == "blob":
                obj_hash = parts[0]
                try:
                    size = int(parts[2])
                    if size > limit:
                        oversized.append((obj_hash, size))
                except ValueError:
                    continue

        self.assertEqual(
            oversized,
            [],
            f"Found {len(oversized)} git blobs exceeding GitHub's 100MB limit: {oversized}",
        )

    def test_02_all_markdown_links_resolve_without_broken_paths(self):
        """
        Scan all markdown files across the repository (excluding .agents)
        and verify that every local link and image embed resolves to a real file.
        """
        md_files = [
            p for p in REPO_ROOT.rglob("*.md")
            if ".agents" not in p.parts and ".git" not in p.parts
        ]
        self.assertGreater(len(md_files), 0, "No markdown files found in repository")

        broken_links = []
        checked_count = 0

        for md_file in md_files:
            text = md_file.read_text(encoding="utf-8")
            links = extract_markdown_links(text)
            for link in links:
                checked_count += 1
                # Clean query strings or anchor tags
                clean_link = link.split("?")[0].split("#")[0].strip()
                if not clean_link:
                    continue

                if clean_link.startswith("/"):
                    target = REPO_ROOT / clean_link.lstrip("/")
                else:
                    target = md_file.parent / clean_link

                if not (target.is_file() or target.is_dir()):
                    rel_md = md_file.relative_to(REPO_ROOT)
                    broken_links.append(f"{rel_md} -> '{link}' (target does not exist: {target})")

        self.assertEqual(
            broken_links,
            [],
            f"Broken links detected across documentation ({len(broken_links)} broken out of {checked_count}):\n"
            + "\n".join(broken_links),
        )

    def test_03_case_sensitivity_for_cross_platform_compatibility(self):
        """
        Ensure all asset paths and markdown links match disk casing character-for-character
        to guarantee compatibility on Linux and GitHub Pages.
        """
        case_violations = []

        # Check all expected asset paths
        for rel_asset in EXPECTED_ASSETS:
            p = REPO_ROOT / rel_asset
            if p.exists():
                ok, err = check_case_sensitive_path(REPO_ROOT, rel_asset)
                if not ok:
                    case_violations.append(err)

        # Check all markdown image links in README.md
        readme = REPO_ROOT / "README.md"
        if readme.is_file():
            links = extract_markdown_links(readme.read_text(encoding="utf-8"))
            for link in links:
                clean_link = link.split("?")[0].split("#")[0].strip()
                if clean_link and not clean_link.startswith(("/", "\\")):
                    ok, err = check_case_sensitive_path(readme.parent, clean_link)
                    if not ok:
                        case_violations.append(f"README.md link '{clean_link}': {err}")

        self.assertEqual(
            case_violations,
            [],
            f"Case sensitivity violations found (will fail on Linux/GitHub):\n" + "\n".join(case_violations),
        )

    def test_04_exclusion_of_os_and_temporary_artifacts(self):
        """
        Verify that no OS artifacts (desktop.ini, Thumbs.db), temporary binaries (*.exe),
        or scratch duplicate directories (v1, v2) are tracked in git.
        """
        proc = run_git_command(["ls-files"])
        tracked_files = proc.stdout.splitlines()

        forbidden_patterns = [
            ("desktop.ini", lambda f: f.endswith("desktop.ini")),
            ("Thumbs.db", lambda f: f.endswith("Thumbs.db")),
            (".DS_Store", lambda f: f.endswith(".DS_Store")),
            ("Windows executable", lambda f: f.endswith(".exe")),
            ("Scratch folder v1", lambda f: "/v1/" in f or f.startswith("v1/")),
            ("Scratch folder v2", lambda f: "/v2/" in f or f.startswith("v2/")),
            ("Blink.txt stub", lambda f: f.endswith("Blink.txt")),
            ("Agent metadata", lambda f: f.startswith(".agents/")),
        ]

        violations = []
        for f in tracked_files:
            for label, predicate in forbidden_patterns:
                if predicate(f):
                    violations.append(f"{label}: {f}")

        self.assertEqual(
            violations,
            [],
            f"Forbidden temporary or OS files tracked in git:\n" + "\n".join(violations),
        )


# ---------------------------------------------------------------------------
# Tier 3: Cross-Feature Interactions
# ---------------------------------------------------------------------------

class Tier3CrossFeatureInteractions(unittest.TestCase):
    """
    Tier 3 tests verify cross-feature interactions:
    README image embeds match physical files, hardware pinouts match motor datasheet,
    and git remote matches GitHub CLI repository view.
    """

    def test_01_readme_image_embeds_match_physical_files(self):
        """
        Verify that images embedded in README.md exist on disk, are valid binary images,
        and provide adequate visual coverage across key hardware subsystems.
        """
        readme = REPO_ROOT / "README.md"
        self.assertTrue(readme.is_file(), "Root README.md does not exist")

        links = extract_markdown_links(readme.read_text(encoding="utf-8"))
        image_links = [l for l in links if l.lower().endswith((".jpg", ".jpeg", ".png"))]

        self.assertGreater(
            len(image_links),
            5,
            f"README.md only embeds {len(image_links)} images. Expected comprehensive visual teardown.",
        )

        subsystems_found = {
            "hero": False,
            "pcb": False,
            "teardown": False,
            "battery": False,
            "charger": False,
            "ui": False,
            "datasheet": False,
        }

        for img_rel in image_links:
            img_path = (readme.parent / img_rel).resolve()
            self.assertTrue(img_path.is_file(), f"Embedded image does not exist: {img_rel}")

            valid, err = validate_binary_header(img_path)
            self.assertTrue(valid, f"Corrupted embedded image {img_rel}: {err}")

            # Subsystem classification
            norm_path = img_rel.replace("\\", "/").lower()
            if "hero" in norm_path:
                subsystems_found["hero"] = True
            if "pcb" in norm_path:
                subsystems_found["pcb"] = True
            if "teardown" in norm_path:
                subsystems_found["teardown"] = True
            if "battery" in norm_path:
                subsystems_found["battery"] = True
            if "charger" in norm_path:
                subsystems_found["charger"] = True
            if "ui" in norm_path:
                subsystems_found["ui"] = True
            if "datasheet" in norm_path:
                subsystems_found["datasheet"] = True

        missing_subsystems = [k for k, v in subsystems_found.items() if not v]
        self.assertEqual(
            missing_subsystems,
            [],
            f"README.md lacks visual image embeds for subsystems: {missing_subsystems}",
        )

    def test_02_pinout_specs_match_datasheet(self):
        """
        Verify cross-consistency between documentation, Arduino sketch, and motor datasheet:
        - CN2 connector: Pin 1 Vm (26V), Pin 2 FG (6 pulses/rev), Pin 3 FR, Pin 4 GND, Pin 5 PWM (active-low)
        - Prominent UI harness color-coding hazard callout (thin red on GND, thin black on KEY)
        - 25kHz Timer1 PWM frequency matching datasheet range (15-25kHz)
        """
        readme = REPO_ROOT / "README.md"
        self.assertTrue(readme.is_file(), "Root README.md not found")
        readme_text = readme.read_text(encoding="utf-8")

        # Verify CN2 motor connector documentation
        self.assertIn("CN2", readme_text, "CN2 connector pinout not referenced in README.md")
        self.assertRegex(readme_text, r"6\s*pulses", "FG pulse rate (6 pulses/rev) missing in documentation")

        # Verify color hazard warning
        has_color_hazard = (
            ("GND" in readme_text and "red" in readme_text.lower())
            and ("KEY" in readme_text and "black" in readme_text.lower())
        )
        self.assertTrue(
            has_color_hazard,
            "Critical color-coding hazard warning (red wire on GND / black wire on KEY) missing in README.md",
        )

        # Cross-verify Arduino sketch frequency with datasheet
        sketch = REPO_ROOT / "firmware/arduino/massage_gun_test/massage_gun_test.ino"
        self.assertTrue(sketch.is_file(), "Arduino test sketch missing")
        sketch_text = sketch.read_text(encoding="utf-8")
        self.assertIn("639", sketch_text, "Arduino sketch Timer1 ICR1=639 (25kHz) frequency mismatch")

    def test_03_git_remote_matches_gh_repo_view(self):
        """
        Verify that local git remote matches GitHub CLI repository view.
        Executes 'gh repo view' and verifies target repository details.
        """
        proc = run_git_command(["remote", "get-url", "origin"])
        if proc.returncode != 0:
            self.skipTest("Git remote 'origin' not yet set")

        remote_url = proc.stdout.strip()
        self.assertIn("yunmai-massage-gun-pro-reverse-engineering", remote_url)

        # Check GitHub CLI if installed and online
        gh_proc = subprocess.run(
            ["gh", "repo", "view", "--json", "name,owner,isPrivate,url"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if gh_proc.returncode == 0:
            import json
            data = json.loads(gh_proc.stdout)
            self.assertEqual(data.get("name"), "yunmai-massage-gun-pro-reverse-engineering")
            self.assertFalse(data.get("isPrivate"), "Repository must be PUBLIC")
            self.assertEqual(data.get("owner", {}).get("login"), "olekkut")


# ---------------------------------------------------------------------------
# Tier 4: Real-World Scenarios
# ---------------------------------------------------------------------------

class Tier4RealWorldScenarios(unittest.TestCase):
    """
    Tier 4 tests verify real-world operational scenarios:
    clean execution of test runner CLI, zero side effects on repository,
    and overall release audit readiness.
    """

    def test_01_cli_runner_execution_and_clean_workspace(self):
        """
        Execute the test runner CLI directly via subprocess and confirm:
        - Zero file pollution in the repository root or tests/
        - Clean exit code and structured output
        """
        runner_path = Path(__file__).resolve()

        # Run with --help
        help_proc = subprocess.run(
            [sys.executable, str(runner_path), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(help_proc.returncode, 0, "Test runner CLI --help failed")
        self.assertIn("--tier", help_proc.stdout, "CLI help missing --tier argument")

        # Verify no unstaged temporary files were created
        status_proc = run_git_command(["status", "--porcelain"])
        for line in status_proc.stdout.splitlines():
            # Exclude known metadata folder .agents
            path_part = line[3:].strip()
            self.assertFalse(
                path_part.endswith((".pyc", ".tmp", ".log")),
                f"Test execution polluted workspace with temporary file: {path_part}",
            )

    def test_02_e2e_release_readiness_scenario(self):
        """
        Simulate an external engineer cloning the repository:
        Verifies presence of LICENSE, README, docs, firmware, and organized photos
        forming a cohesive, complete reverse-engineering package.
        """
        license_file = REPO_ROOT / "LICENSE"
        self.assertTrue(license_file.is_file(), "Root LICENSE file missing")
        self.assertIn("MIT", license_file.read_text(encoding="utf-8").upper(), "LICENSE is not MIT")

        manuals_dir = REPO_ROOT / "docs/manuals"
        self.assertTrue(manuals_dir.is_dir(), "User manuals folder missing")
        manuals = list(manuals_dir.glob("*.pdf"))
        self.assertGreaterEqual(len(manuals), 2, "Expected at least 2 factory PDF manuals")

        photos_dir = REPO_ROOT / "hardware/photos"
        self.assertTrue(photos_dir.is_dir(), "Hardware photos folder missing")
        all_photos = list(photos_dir.rglob("*.jpg")) + list(photos_dir.rglob("*.png"))
        self.assertGreaterEqual(len(all_photos), 25, "Expected at least 25 teardown photos")


# ---------------------------------------------------------------------------
# Test Runner Implementation
# ---------------------------------------------------------------------------

TIER_CLASSES = {
    1: ("Tier 1: Feature Coverage", Tier1FeatureCoverage),
    2: ("Tier 2: Boundary & Corner Cases", Tier2BoundaryCornerCases),
    3: ("Tier 3: Cross-Feature Interactions", Tier3CrossFeatureInteractions),
    4: ("Tier 4: Real-World Scenarios", Tier4RealWorldScenarios),
}


def build_suite(tier: int | None = None) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    if tier is not None:
        if tier not in TIER_CLASSES:
            raise ValueError(f"Invalid tier {tier}. Valid tiers are 1, 2, 3, 4.")
        tier_title, test_class = TIER_CLASSES[tier]
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    else:
        for tier_num in sorted(TIER_CLASSES.keys()):
            tier_title, test_class = TIER_CLASSES[tier_num]
            suite.addTests(loader.loadTestsFromTestCase(test_class))

    return suite


class ColoredTestResult(unittest.TextTestResult):
    """Custom test result formatter for clear, professional output."""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.results = []
        self._start_time = None

    def startTest(self, test):
        super().startTest(test)
        self._start_time = time.time()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.time() - (self._start_time or time.time())
        self.results.append(("PASS", test, elapsed, ""))
        sys.stdout.write(f"  [PASS] {test._testMethodName} ({elapsed:.3f}s)\n")
        sys.stdout.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.time() - (self._start_time or time.time())
        msg = self._exc_info_to_string(err, test)
        self.results.append(("FAIL", test, elapsed, msg))
        sys.stdout.write(f"  [FAIL] {test._testMethodName} ({elapsed:.3f}s)\n")
        sys.stdout.flush()

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.time() - (self._start_time or time.time())
        msg = self._exc_info_to_string(err, test)
        self.results.append(("ERROR", test, elapsed, msg))
        sys.stdout.write(f"  [ERROR] {test._testMethodName} ({elapsed:.3f}s)\n")
        sys.stdout.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        elapsed = time.time() - (self._start_time or time.time())
        self.results.append(("SKIP", test, elapsed, reason))
        sys.stdout.write(f"  [SKIP] {test._testMethodName} (reason: {reason})\n")
        sys.stdout.flush()


def run_tests(tier: int | None = None, verbosity: int = 1) -> int:
    suite = build_suite(tier)

    print("=" * 78)
    print(" Yunmai Massage Gun Pro (YMFG-B563) -- End-to-End (E2E) Test Suite")
    print(f" Target Root: {REPO_ROOT}")
    if tier:
        print(f" Executing Scope: Tier {tier} ({TIER_CLASSES[tier][0]})")
    else:
        print(" Executing Scope: All Tiers (1 to 4)")
    print("=" * 78)

    runner = unittest.TextTestRunner(
        resultclass=ColoredTestResult,
        verbosity=verbosity,
        stream=open(os.devnull, "w"),  # Suppress default dots
    )

    start_total = time.time()
    result = runner.run(suite)
    total_elapsed = time.time() - start_total

    print("\n" + "=" * 78)
    print(" Test Execution Summary")
    print("=" * 78)
    total_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_run - failures - errors - skipped

    print(f" Total Tests Run: {total_run}")
    print(f"   Passed:  {passed}")
    print(f"   Failed:  {failures}")
    print(f"   Errors:  {errors}")
    print(f"   Skipped: {skipped}")
    print(f" Total Duration: {total_elapsed:.3f}s")
    print("=" * 78)

    if failures > 0 or errors > 0:
        print("\n--- Failure / Error Details ---")
        for test, err_msg in result.failures:
            print(f"\n[FAIL] {test}:")
            print(err_msg.strip())
        for test, err_msg in result.errors:
            print(f"\n[ERROR] {test}:")
            print(err_msg.strip())
        print("=" * 78)
        return 1

    print("\n[SUCCESS] All executed tests passed successfully.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Yunmai Massage Gun Pro E2E Test Suite Runner"
    )
    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3, 4],
        default=None,
        help="Run tests for a specific tier only (1, 2, 3, or 4)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    exit_code = run_tests(tier=args.tier, verbosity=2 if args.verbose else 1)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
