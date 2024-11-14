#!/usr/bin/env python3

import argparse
import re
import subprocess
from pathlib import Path
import sys

class VersionChecker:
    def __init__(self):
        self.version_pattern = re.compile(r'^\d+\.\d+\.\d+(?:-rc\d+)?$')

    def _parse_cmake_version(self, cmake_file: Path) -> str:
        """Extract version from CMakeLists.txt"""
        content = cmake_file.read_text()

        # Extract PROJECT VERSION
        project_version_pattern = r'PROJECT\s*\([^)]*VERSION\s+(\d+\.\d+\.\d+)[^)]*\)'
        version_match = re.search(project_version_pattern, content, re.MULTILINE | re.IGNORECASE)

        if version_match:
            version = version_match.group(1)
        else:
            # Fallback to old format
            def extract_value(key: str) -> str:
                pattern = f'^[^#]*SET\\({key}[\\s]*"([^"]*)"\\)'
                match = re.search(pattern, content, re.MULTILINE)
                return match.group(1) if match else None

            major = extract_value("CMAKE_PROJECT_VERSION_MAJOR")
            minor = extract_value("CMAKE_PROJECT_VERSION_MINOR")
            patch = extract_value("CMAKE_PROJECT_VERSION_PATCH")

            if not all([major, minor, patch]):
                raise ValueError("Could not extract version components")

            version = f"{major}.{minor}.{patch}"

        # Check for RC version
        rc_pattern = r'^[^#]*SET\s*\((?:RC_VERSION|CMAKE_PROJECT_VERSION_RC)\s*"(\d+)"\s*\)'
        rc_match = re.search(rc_pattern, content, re.MULTILINE)

        if rc_match:
            version = f"{version}-rc{rc_match.group(1)}"

        return version

    def check_version(self, tag: str = None):
        """
        Check version consistency between CMakeLists.txt and git tag
        Args:
            tag: Optional git tag to check against
        """
        try:
            version = self._parse_cmake_version(Path("CMakeLists.txt"))
            print(f"Version in 'CMakeLists.txt' file: '{version}'")

            if tag:
                print(f"Input tag: '{tag}'")
                print("Release mode: check version consistency...")
                if tag != version:
                    print(f"ERROR: the tag '{tag}' is different from the version '{version}' in the 'CMakeLists.txt' file")
                    sys.exit(1)
                print(f"Version consistency check passed: tag '{tag}' matches CMake version '{version}'")
            else:
                print("Snapshot mode: fetch existing tags...")
                subprocess.run(["git", "fetch", "--tags"], check=True)

                result = subprocess.run(
                    ["git", "tag", "-l", version],
                    capture_output=True,
                    text=True,
                    check=True
                )

                if result.stdout.strip():
                    print(f"ERROR: version '{version}' has already been released")
                    sys.exit(1)
                print(f"Version '{version}' has not been released yet")

        except Exception as e:
            print(f"ERROR: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check version consistency")
    parser.add_argument("tag", nargs="?", help="Git tag to check against (optional)")
    args = parser.parse_args()

    checker = VersionChecker()
    checker.check_version(args.tag)