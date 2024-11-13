#!/usr/bin/env python3

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from packaging.version import parse, Version, InvalidVersion

class DocumentationManager:
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.gh_pages_branch = "gh-pages"
        # Pattern to match version directories (x.y.z optionally followed by -rc<n> and/or -SNAPSHOT)
        self.version_pattern = re.compile(r'^\d+\.\d+\.\d+(?:-rc\d+)?(?:-SNAPSHOT)?$')

    def _parse_cmake_version(self, cmake_file: Path) -> str:
        """Extract version from CMakeLists.txt"""
        content = cmake_file.read_text()

        def extract_value(key: str) -> str:
            pattern = f'SET\\({key}[\\s]*"([^"]*)"\\)'
            match = re.search(pattern, content, re.MULTILINE)
            return match.group(1) if match else None

        major = extract_value("CMAKE_PROJECT_VERSION_MAJOR")
        minor = extract_value("CMAKE_PROJECT_VERSION_MINOR")
        patch = extract_value("CMAKE_PROJECT_VERSION_PATCH")
        rc = extract_value("CMAKE_PROJECT_VERSION_RC")

        version = f"{major}.{minor}.{patch}"
        if rc:
            return f"{version}-rc{rc}-SNAPSHOT"
        return f"{version}-SNAPSHOT"

    def _get_version_key(self, version_str: str) -> tuple:
        """
        Create a sortable key for version ordering
        Returns a tuple to ensure proper sorting:
        - Base version components (major, minor, patch) first
        - Then a category number:
          0 for stable versions (first)
          1 for RC versions (middle, with RC number negated to sort higher numbers first)
          2 for SNAPSHOT versions (last)
        """
        try:
            base_version = version_str.split('-')[0]
            v = parse(base_version)
            base = (v.major, v.minor, v.micro)

            if "SNAPSHOT" in version_str:
                return base + (2,)  # SNAPSHOT versions last
            elif "rc" in version_str.lower():
                rc_num = int(version_str.lower().split("rc")[1].split("-")[0])
                return base + (1, -rc_num)  # RC versions in middle, higher RC numbers first
            return base + (0,)  # Stable versions first
        except InvalidVersion:
            return (0, 0, 0, 999)  # Invalid versions last

    def prepare_documentation(self, version: str = None):
        """
        Main method to prepare documentation
        - Clones gh-pages branch
        - Cleans up existing SNAPSHOT versions if publishing a release
        - Creates version directory and copies documentation
        - Updates latest symlink for stable versions
        - Generates version list
        """
        if not version:
            version = self._parse_cmake_version(Path("CMakeLists.txt"))
        print(f"Using version: {version}")

        # Clone gh-pages branch
        repo_name = Path.cwd().name
        dest_dir = Path(repo_name)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        subprocess.run(["git", "clone", "-b", self.gh_pages_branch, self.repo_url, repo_name], check=True)

        # Clean up SNAPSHOT versions if this is a release
        if not version.endswith("-SNAPSHOT"):
            base_version = version.split("-rc")[0]
            snapshots = list(dest_dir.glob(f"{base_version}*-SNAPSHOT"))
            for snapshot in snapshots:
                print(f"Removing SNAPSHOT directory: {snapshot}")
                shutil.rmtree(snapshot)

        # Create version directory and copy documentation
        version_dir = dest_dir / version
        version_dir.mkdir(exist_ok=True)

        doxygen_out = Path(".github/doxygen/out/html")
        if doxygen_out.exists():
            shutil.copytree(doxygen_out, version_dir, dirs_exist_ok=True)

        # Update latest symlink for stable versions only (no SNAPSHOT, no RC)
        if not any(x in version for x in ["-SNAPSHOT", "-rc"]):
            latest_link = dest_dir / "latest"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(version)

            # Update robots.txt to allow indexing of latest version only
            robots_txt = dest_dir / "robots.txt"
            robots_txt.write_text(
                "User-agent: *\n"
                "Allow: /\n"
                "Allow: /latest/\n"
                "Disallow: /*/[0-9]*/\n"
            )

        # Generate versions list
        self._generate_versions_list(dest_dir)

    def _generate_versions_list(self, docs_dir: Path):
        """
        Generate the versions list markdown file
        Only includes directories matching the version pattern: x.y.z[-rcN][-SNAPSHOT]
        Versions are sorted with most recent first:
        - Stable versions (e.g., 2.1.0)
        - RC versions (e.g., 2.1.0-rc2 before 2.1.0-rc1)
        - SNAPSHOT versions
        """
        versions_file = docs_dir / "list_versions.md"

        # Get only version directories that match the pattern
        versions = [
            d.name for d in docs_dir.iterdir()
            if d.is_dir() and self.version_pattern.match(d.name)
        ]

        # Sort versions
        sorted_versions = sorted(versions, key=self._get_version_key)

        # Generate markdown
        with versions_file.open("w") as f:
            f.write("| Version | Documents |\n")
            f.write("|:---:|---|\n")

            # Add latest link if it exists (stable versions only)
            if (docs_dir / "latest").exists():
                f.write("| latest | [API documentation](latest) |\n")

            # Add all versions in reverse order (most recent first)
            for version in reversed(sorted_versions):
                f.write(f"| {version} | [API documentation]({version}) |\n")

        print("Generated versions list:")
        print(versions_file.read_text())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare API documentation")
    parser.add_argument("version", nargs="?", help="Version to publish (optional)")
    args = parser.parse_args()

    manager = DocumentationManager("https://github.com/eclipse-keypop/keypop-card-cpp-api.git")
    manager.prepare_documentation(args.version)