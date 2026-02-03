# Monorepo Scaffold Operational Notes

Use this reference when you need deeper context on what the scaffold script does or when something goes wrong.

## Guardrails Recap
- Never create directories outside the repository root passed to the script.
- Governance docs **must** match the mandated content exactly; do not customize when running the scaffold.
- The script is idempotent: re-running should not destroy existing phase work, but it will reapply governance docs and Spec-Kit config.

## Script Inputs
- **Arg 1 (optional):** Absolute path to repo root. Defaults to `pwd` if omitted.
- Requires Bash 4+, `mkdir`, and standard POSIX utilities already available in the CLI container.

## Output Breakdown
1. **Directories:** `specs/`, `.spec-kit/`, and every `phases/phase-*` folder are created with `mkdir -p`.
2. **Governance Files:** CLAUDE.md, AGENTS.md, README.md are overwritten each run—expect no merge prompts.
3. **Spec Templates:** Created only when missing. Existing files are left untouched to preserve authored specs.
4. **pyproject.toml:** Only created when absent; otherwise the script prints a reminder to verify uv configuration manually.

## Troubleshooting
- **"Permission denied"**: Ensure the path provided is writable. Use `ls -ld <path>` to confirm ownership.
- **"command not found" when running script**: Make sure you invoke via `bash scripts/scaffold_monorepo.sh ...` and that the file has execute permissions (`chmod +x`).
- **Spec headings missing after manual edits**: Delete or rename the offending spec file and re-run the script to regenerate the template, then reapply content.
- **pyproject already customized**: The script will not overwrite; manually confirm `[tool.uv.workspace]` matches the five phases.

## Manual Verification Tips
- Run `ls specs phases .spec-kit` to confirm directory presence.
- Use `rg -n "No Task = No Code" AGENTS.md` to ensure governance text is intact.
- Inspect `.spec-kit/config.yaml` whenever phases are renamed—it must stay in sync with actual folders.
- If new phases are added in the future, update both the script and config mapping simultaneously.

Keep this reference lean—augment only with precise troubleshooting steps or new guardrails discovered in practice.