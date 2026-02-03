#!/usr/bin/env python3
"""
Validate the OpenAI ChatKit Implementation skill before packaging
"""

import yaml
from pathlib import Path
import sys

def validate_skill():
    skill_dir = Path(__file__).parent.parent

    # Check if required files exist
    required_files = [
        skill_dir / "SKILL.md",
    ]

    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Missing required file: {file_path}")
            return False

    # Validate SKILL.md has proper frontmatter
    skill_md = skill_dir / "SKILL.md"
    with open(skill_md, 'r') as f:
        content = f.read()

    if not content.strip().startswith("---"):
        print("❌ SKILL.md must start with YAML frontmatter (---)")
        return False

    # Extract frontmatter
    parts = content.split("---", 2)
    if len(parts) < 3:
        print("❌ SKILL.md must contain YAML frontmatter (--- content ---)")
        return False

    frontmatter = parts[1]
    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML frontmatter in SKILL.md: {e}")
        return False

    # Check required frontmatter fields
    if not data:
        print("❌ SKILL.md frontmatter is empty")
        return False

    if "name" not in data:
        print("❌ SKILL.md frontmatter missing 'name' field")
        return False

    if "description" not in data:
        print("❌ SKILL.md frontmatter missing 'description' field")
        return False

    name = data["name"]
    description = data["description"]

    if not name or not isinstance(name, str):
        print("❌ 'name' field must be a non-empty string")
        return False

    if not description or not isinstance(description, str):
        print("❌ 'description' field must be a non-empty string")
        return False

    # Check that name is a valid identifier
    if not name.replace("_", "").replace("-", "").isalnum():
        print("❌ 'name' field must be alphanumeric with underscores/hyphens only")
        return False

    print(f"✅ Skill name: {name}")
    print(f"✅ Description length: {len(description)} characters")

    # Check for reasonable description length
    if len(description) < 20:
        print("⚠️  Description seems quite short, consider adding more detail about when to use this skill")

    # Check that description contains trigger information
    desc_lower = description.lower()
    if not any(trigger in desc_lower for trigger in ["when", "use", "help", "assist", "chatkit", "implementation", "openai", "frontend"]):
        print("⚠️  Description should include information about when to use this skill")

    print("✅ Skill validation passed!")
    return True

if __name__ == "__main__":
    if validate_skill():
        sys.exit(0)
    else:
        sys.exit(1)