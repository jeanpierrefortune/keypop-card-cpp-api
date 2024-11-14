#!/usr/bin/env python3

import argparse
import os
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
        try:
            base_version = version_str.split('-')[0]
            v = parse(base_version)
            base = (v.major, v.minor, v.micro)

            if "rc" in version_str.lower():                  # Test RC first
                rc_num = int(version_str.lower().split("rc")[1].split("-")[0])
                if "SNAPSHOT" in version_str:
                    return base + (0, rc_num)                # RC SNAPSHOT first
                return base + (1, rc_num)                    # Released RC second
            if "SNAPSHOT" in version_str:                    # Base SNAPSHOT last
                return base + (2, 0)
            return base + (3, 0)                            # Stable version (not used here)

        except InvalidVersion:
            return (0, 0, 0, 999)

    def prepare_documentation(self, version: str = None):
        """Main method to prepare documentation"""
        if not version:
            version = self._parse_cmake_version(Path("CMakeLists.txt"))
        print(f"Using version: {version}")

        # Get repository name as done in the bash script
        repo_name = Path.cwd().name
        dest_dir = Path(repo_name)

        print(f"Clone {repo_name}...")
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        subprocess.run(["git", "clone", "-b", self.gh_pages_branch, self.repo_url, repo_name], check=True)

        # Change to the cloned directory
        os.chdir(dest_dir)

        print("Delete existing SNAPSHOT directory...")
        if not version.endswith("-SNAPSHOT"):
            # For RC release (e.g., "2.1.0-rc1")
            if "-rc" in version:
                # Only delete the corresponding RC SNAPSHOT
                rc_snapshot = f"{version}-SNAPSHOT"
                snapshot_path = Path(rc_snapshot)
                if snapshot_path.exists():
                    print(f"Removing RC SNAPSHOT directory: {snapshot_path}")
                    shutil.rmtree(snapshot_path)
            # For final release (e.g., "2.1.0")
            else:
                # Only delete the corresponding version SNAPSHOT
                version_snapshot = f"{version}-SNAPSHOT"
                snapshot_path = Path(version_snapshot)
                if snapshot_path.exists():
                    print(f"Removing version SNAPSHOT directory: {snapshot_path}")
                    shutil.rmtree(snapshot_path)

        print(f"Create target directory {version}...")
        version_dir = Path(version)
        version_dir.mkdir(exist_ok=True)

        print("Copy Doxygen doc...")
        doxygen_out = Path("../.github/doxygen/out/html")
        if doxygen_out.exists():
            # Copy contents of html directory into version directory
            for item in doxygen_out.glob("*"):
                if item.is_dir():
                    shutil.copytree(item, version_dir / item.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, version_dir)
        else:
            raise FileNotFoundError(f"Doxygen output directory not found at {doxygen_out}")

        if not any(x in version for x in ["-SNAPSHOT", "-rc"]):
            print("Creating latest symlink...")
            latest_link = Path("latest")
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(version)

            print("Writing robots.txt...")
            robots_txt = Path("robots.txt")
            robots_txt.write_text(
                "User-agent: *\n"
                "Allow: /\n"
                "Allow: /latest/\n"
                "Disallow: /*/[0-9]*/\n"
            )

        print("Generating versions list...")
        self._generate_versions_list(Path('.'))

        # Return to original directory
        os.chdir("..")

    def _generate_versions_list(self, docs_dir: Path):
       """Generate the versions list markdown file"""
       versions_file = Path("list_versions.md")

       print("Looking for version directories")
       versions = []
       for d in Path('.').glob('*'):
           if d.is_dir() and self.version_pattern.match(d.name):
               print(f"Found version directory: {d.name}")
               versions.append(d.name)
           elif d.is_dir():
               print(f"Skipping non-version directory: {d.name}")

       print(f"All found versions before sorting: {versions}")
       sorted_versions = sorted(versions, key=self._get_version_key)
       print(f"Sorted versions: {sorted_versions}")

       with versions_file.open("w") as f:
           f.write("| Version | Documents |\n")
           f.write("|:---:|---|\n")

           if Path("latest").exists():
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