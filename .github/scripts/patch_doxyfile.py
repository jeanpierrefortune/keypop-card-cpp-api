#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

class DoxyfileUpdater:
    def _parse_cmake_version(self, cmake_file: Path) -> str:
        """
        Extract version from CMakeLists.txt using:
        - Base version from PROJECT VERSION
        - Optional RC from RC_VERSION
        Returns version string with appropriate suffix (-rcN or -SNAPSHOT)
        """
        content = cmake_file.read_text()

        # Extract base version from PROJECT
        project_version_pattern = r'PROJECT\s*\([^)]*VERSION\s+(\d+\.\d+\.\d+)[^)]*\)'
        version_match = re.search(project_version_pattern, content, re.MULTILINE | re.IGNORECASE)

        if not version_match:
            raise ValueError("Could not extract PROJECT VERSION")

        version = version_match.group(1)

        # Look for RC version
        rc_pattern = r'^[^#]*SET\s*\(RC_VERSION\s*"(\d+)"\s*\)'
        rc_match = re.search(rc_pattern, content, re.MULTILINE)

        if rc_match:
            # RC version is set and not commented
            return f"{version}-rc{rc_match.group(1)}"

        # For SNAPSHOT versions, check if this is a release version
        package_pattern = r'SET\s*\(PACKAGE_VERSION\s*"\$\{PROJECT_VERSION\}"\s*\)'
        is_release = bool(re.search(package_pattern, content, re.MULTILINE))

        # Add SNAPSHOT suffix if not a release
        if not is_release:
            return f"{version}-SNAPSHOT"

        return version

    def update_doxyfile(self, version: str = None):
        """
        Update Doxyfile with current version
        Args:
            version: Optional version string, if not provided will be extracted from CMakeLists.txt
        """
        print("Compute the current API version...")

        if not version:
            try:
                version = self._parse_cmake_version(Path("CMakeLists.txt"))
            except Exception as e:
                print(f"ERROR: Failed to parse version: {str(e)}")
                raise

        print(f"Computed current API version: {version}")

        # Update Doxyfile
        doxyfile_path = Path(".github/doxygen/Doxyfile")
        if not doxyfile_path.exists():
            raise FileNotFoundError(f"Doxyfile not found at {doxyfile_path}")

        content = doxyfile_path.read_text()
        updated_content = content.replace("%PROJECT_VERSION%", version)
        doxyfile_path.write_text(updated_content)

        print(f"Updated {doxyfile_path} with version {version}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Doxyfile version")
    parser.add_argument("version", nargs="?", help="Version to set (optional)")
    args = parser.parse_args()

    updater = DoxyfileUpdater()
    updater.update_doxyfile(args.version)