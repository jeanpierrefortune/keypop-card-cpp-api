#!/usr/bin/env python3

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from packaging.version import parse, Version, InvalidVersion

class DocumentationManager:
    def __init__(self, github_org: str, repo_name: str):
        self.repo_url = f"https://github.com/{github_org}/{repo_name}.git"
        self.gh_pages_branch = "gh-pages"
        self.version_pattern = re.compile(r'^\d+\.\d+\.\d+(?:-rc\d+)?(?:-SNAPSHOT)?$')

    def _parse_cmake_version(self, cmake_file: Path) -> str:
        """
        Extract version from CMakeLists.txt
        Handles both PROJECT VERSION and RC_VERSION
        """
        content = cmake_file.read_text()

        # Extract PROJECT VERSION
        project_version_pattern = r'PROJECT\s*\([^)]*VERSION\s+(\d+\.\d+\.\d+)[^)]*\)'
        version_match = re.search(project_version_pattern, content, re.MULTILINE | re.IGNORECASE)
        if not version_match:
            raise ValueError("Could not extract PROJECT VERSION")
        version = version_match.group(1)

        # Extract RC_VERSION if not commented
        rc_pattern = r'^[^#]*SET\s*\(RC_VERSION\s*"(\d+)"\s*\)'
        rc_match = re.search(rc_pattern, content, re.MULTILINE)

        # If this is not a release version, append SNAPSHOT
        if rc_match:
            # RC version found and not commented
            return f"{version}-rc{rc_match.group(1)}-SNAPSHOT"
        else:
            # No RC version or RC version is commented
            return f"{version}-SNAPSHOT"

    def _get_version_key(self, version_str: str) -> tuple:
        """Create a sortable key for version ordering"""
        try:
            base_version = version_str.split('-')[0]
            v = parse(base_version)
            base = (v.major, v.minor, v.micro)

            if "SNAPSHOT" in version_str:
                return base + (2,)
            elif "rc" in version_str.lower():
                rc_num = int(version_str.lower().split("rc")[1].split("-")[0])
                return base + (1, -rc_num)
            return base + (0,)
        except InvalidVersion:
            return (0, 0, 0, 999)

def prepare_documentation(self, version: str = None):
    """Main method to prepare documentation"""
    if not version:
        version = self._parse_cmake_version(Path("CMakeLists.txt"))
    print(f"Using version: {version}")

    repo_name = Path.cwd().name
    dest_dir = Path(repo_name)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    subprocess.run(["git", "clone", "-b", self.gh_pages_branch, self.repo_url, repo_name], check=True)

    print(f"DEBUG: Current directories before cleanup: {list(dest_dir.glob('*'))}")

    # Clean up SNAPSHOT versions if this is a release
    if not version.endswith("-SNAPSHOT"):
        if "-rc" in version:
            rc_snapshot = f"{version}-SNAPSHOT"
            snapshot_dir = dest_dir / rc_snapshot
            if snapshot_dir.exists():
                print(f"Removing RC SNAPSHOT directory: {snapshot_dir}")
                shutil.rmtree(snapshot_dir)
        else:
            base_version = version
            snapshot_dir = dest_dir / f"{base_version}-SNAPSHOT"
            if snapshot_dir.exists():
                print(f"Removing SNAPSHOT directory: {snapshot_dir}")
                shutil.rmtree(snapshot_dir)

        print(f"DEBUG: Current directories after cleanup: {list(dest_dir.glob('*'))}")

        version_dir = dest_dir / version
        version_dir.mkdir(exist_ok=True)

        doxygen_out = Path(".github/doxygen/out/html")
        if doxygen_out.exists():
            shutil.copytree(doxygen_out, version_dir, dirs_exist_ok=True)

        if not any(x in version for x in ["-SNAPSHOT", "-rc"]):
            latest_link = dest_dir / "latest"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(version)

            robots_txt = dest_dir / "robots.txt"
            robots_txt.write_text(
                "User-agent: *\n"
                "Allow: /\n"
                "Allow: /latest/\n"
                "Disallow: /*/[0-9]*/\n"
            )

        self._generate_versions_list(dest_dir)

    def _generate_versions_list(self, docs_dir: Path):
        """Generate the versions list markdown file"""
        versions_file = docs_dir / "list_versions.md"

        print("DEBUG: Looking for version directories")
        versions = []
        for d in docs_dir.iterdir():
            if d.is_dir() and self.version_pattern.match(d.name):
                print(f"DEBUG: Found version directory: {d.name}")
                versions.append(d.name)
            elif d.is_dir():
                print(f"DEBUG: Skipping non-version directory: {d.name}")

        print(f"DEBUG: All found versions before sorting: {versions}")
        sorted_versions = sorted(versions, key=self._get_version_key)
        print(f"DEBUG: Sorted versions: {sorted_versions}")

        with versions_file.open("w") as f:
            f.write("| Version | Documents |\n")
            f.write("|:---:|---|\n")

            if (docs_dir / "latest").exists():
                f.write("| latest | [API documentation](latest) |\n")

            for version in reversed(sorted_versions):
                f.write(f"| {version} | [API documentation]({version}) |\n")

        print("Generated versions list:")
        print(versions_file.read_text())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare API documentation")
    parser.add_argument("--github-org", required=True, help="GitHub organization name")
    parser.add_argument("--repo-name", required=True, help="Repository name")
    parser.add_argument("--version", help="Version to publish (optional)")
    args = parser.parse_args()

    manager = DocumentationManager(args.github_org, args.repo_name)
    manager.prepare_documentation(args.version)