# Installation and portability

[Documentation](../index.md) · [中文](../zh-CN/installation.md) · [Usage](usage.md)

## Requirements

| Capability | Requirement |
|---|---|
| Workspace, checks, MD/HTML/DOCX | Python 3.10+ standard library |
| Real research | A host agent with a model, document/file tools, and access to relevant primary sources |
| Rich PDF publisher | Optional `requirements-report.txt` packages and legally available body/heading fonts |
| Data charts | Optional matplotlib, pandas, numpy; real data supplied by the researcher |
| Technical visual interpretation | An image-capable model or human review, if claimed |
| Parallel research | Optional host delegation; single-agent operation remains supported |

No market-data API key or model account is distributed. Optional upstream tools may have their own dependencies, permissions, and network needs; running `doctor` does not install them.

## Install the Skill folder

From the repository root:

```bash
python skills/ai-investment-research/scripts/research.py doctor
python skills/ai-investment-research/scripts/install.py \
  --target /absolute/path/to/host/skills --mode copy --dry-run
python skills/ai-investment-research/scripts/install.py \
  --target /absolute/path/to/host/skills --mode copy
```

`--target` is the **parent** skill directory. The installed child is `ai-investment-research`. Copy mode is independent of the checkout. Link mode points the host at this checkout and requires that it remain in place:

```bash
python skills/ai-investment-research/scripts/install.py \
  --target /absolute/path/to/host/skills --mode link
```

The installer must refuse an existing different skill. Move or choose an alternate target deliberately; the installer does not delete it or replace a different junction. For an existing same-content copy, read the actual result rather than assuming an upgrade occurred.

For Codex, use its configured `skills` directory, commonly `~/.codex/skills`. Other hosts may require importing the folder or refreshing the skill catalog. A successful copy is not proof of host discovery: ask that host to load `$ai-investment-research` and confirm the entry is readable.

## Windows

Python commands work from PowerShell with quoted paths. A continuation example in this documentation uses Bash `\`; in PowerShell put the command on one line or use PowerShell backticks.

```powershell
python skills/ai-investment-research/scripts/install.py --target "$env:USERPROFILE/.codex/skills" --mode copy
```

Link mode may require OS permission for symlinks. The legacy [junction helper](../../skills/ai-investment-research/scripts/install_local.ps1) is Windows-specific and requires an explicit DSH root when it cannot infer one. It refuses unrelated existing entries. The portable Python installer is the primary path.

## Report dependencies and fonts

Use an environment you control:

```bash
python -m venv .venv
# Activate it using your platform's normal command.
python -m pip install -r skills/ai-investment-research/requirements-report.txt
```

The publisher accepts `--font-body`, `--font-head`, or `AIR_FONT_BODY` / `AIR_FONT_HEAD`. Windows fallback is available only when the expected local fonts exist. For Chinese PDFs on Linux/macOS, provide a compatible installed CJK TTF/TTC; do not assume Latin fonts contain Chinese glyphs. For English-only input, use appropriate local fonts and verify the real output. No proprietary font files are shipped.

```bash
python skills/ai-investment-research/scripts/publisher.py --help
```

If a font format cannot be embedded by ReportLab, choose a compatible font rather than silently replacing Chinese text with boxes. Font availability and output geometry are separate checks from visual review.

## Project location

The public settings file has no private absolute workspace. The agent can use `reports/` under the current project or a user-specified directory. The core CLI still requires an explicit absolute `--output`; settings are agent guidance, not a hidden CLI directory resolver.

Install resources and research artifacts are separate. Do not write user runs into the installed Skill or commit them into this repository.

## Verify installation

```bash
python tools/demo.py --output /absolute/path/to/new-synthetic-run
python tools/verify_repo.py
```

The first command is offline and uses fabricated figures. The second checks repository packaging and source integrity. Neither establishes live source access, model quality, financial truth, or forecast accuracy. See [quality and limits](quality-and-limits.md).
