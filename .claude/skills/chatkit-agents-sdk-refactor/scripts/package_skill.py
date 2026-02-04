#!/usr/bin/env python3
"""
Package the ChatKit + Agents SDK Refactor skill into a distributable .skill file
"""

import zipfile
import os
from pathlib import Path

def package_skill():
    skill_dir = Path(__file__).parent.parent
    skill_name = skill_dir.name

    # Create the package file
    package_file = skill_dir.parent / f"{skill_name}.skill"

    with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files in the skill directory
        for root, dirs, files in os.walk(skill_dir):
            for file in files:
                file_path = Path(root) / file
                # Skip the package file itself if it already exists
                if file_path == package_file:
                    continue
                # Add file to zip with relative path
                arcname = file_path.relative_to(skill_dir.parent)
                zipf.write(file_path, arcname)

    print(f"Skill packaged successfully: {package_file}")

if __name__ == "__main__":
    package_skill()