# Report publishing

[Documentation](../index.md) · [中文](../zh-CN/publishing.md) · [Content contract](../../skills/ai-investment-research/references/publisher_contract.md)

## Choose the export route

| Route | Input | Outputs | Dependencies |
|---|---|---|---|
| Core renderer | Written `04_deliverables/report.md` plus research ledgers | MD, standalone HTML, basic DOCX; PDF through an existing supported browser | Python standard library; installed browser for PDF |
| Content publisher | Written structured content JSON and local PNG/JPEG | Paginated PDF, same-source MD, standalone HTML, PDF audit and manifest | ReportLab, PyMuPDF, Pillow and compatible local fonts |

These are alternative rendering sources. The publisher does not run research or check every source claim. Run ledger checks separately. For a custom multi-chart business report, use the content publisher; for a basic Word handoff, use the core renderer. Both can overwrite the run’s `report.md`/`report.html`, so preserve the authoritative source before switching routes.

## Content publisher

```bash
python skills/ai-investment-research/scripts/publisher.py \
  --run /absolute/research-run --content 99_internal/content.json \
  --font-body /local/body.ttf --font-head /local/heading.ttf
```

The top-level content identifies the title, ticker, cutoff, quote note, judgment, filename, up to three cover metrics, and logical pages. Blocks include paragraphs, subheadings, notes, tables, local charts, and source entries. See the complete contract linked above and the [data-contract documentation](data-contracts.md).

Charts must be local PNG/JPEG inside the run. Paths that escape the run are refused. User text is escaped rather than executed as arbitrary HTML. No remote images, scripts, or fonts are fetched. HTML embeds the original chart bytes as data URIs.

## Page layout and actual pagination

The layout uses A4, white background, black body text, restrained horizontal rules, and source captions. Logical pages have explicit starts. Charts preserve aspect ratio and are kept with captions. The table of contents is resolved against actual page starts, not guessed page numbers; PDF bookmarks use those actual destinations.

A logical page can overflow. The manifest then records a different actual page count and a `warning`. That is not permission to hide clipping: check text/image bounds and the actual report. The historical On and Yonyou examples have two-page contents sections, and their reported page counts include them.

## Status and failure handling

| Publisher result | Meaning | Action |
|---|---|---|
| `pass` | Deterministic checks passed | Still inspect facts and, if possible, appearance |
| `warning` | Export exists with disclosed issues such as overflow | Read every warning; actual mapping is authoritative |
| `fail` | Layout/audit checks failed | Repair and rebuild; do not present it as passed |
| Build exception | Content, font or rendering problem | Inspect the current error; an old manifest is not evidence of a new successful build |

Read `99_internal/report_manifest.json` and `pdf-layout-audit.json`; do not rely on a zero exit code alone. `warning` is a non-failure exit. `fail` and build errors use nonzero exits as documented by `--help` and the script.

## What the audit checks

- Real PDF pages and logical-to-actual mapping.
- Text extraction and Chinese-character coverage.
- Text/image geometry against reserved body bounds.
- Blank body pages and chart placement counts.
- Real bookmark targets, source links, input/output hashes.

The audit does not verify chart labels against financial data, distinguish facts from opinions, or establish visual quality. A human or image-capable model must separately review aesthetics and chart internals if that claim is made. If unavailable, state that only structural checks were completed.

## Fonts and licensing

Use CLI font options or `AIR_FONT_BODY` and `AIR_FONT_HEAD`. A compatible installed CJK font is needed for Chinese text. Font discovery is environment-dependent. Do not redistribute proprietary fonts with a report generator or remove missing-glyph warnings to force a pass.

## Preserve the inputs

Keep raw evidence, normalized data, scripts, the source manuscript, content JSON, source/claim/forecast ledgers, and reviews. Share only the deliverables and evidence the user authorized. A publishing request is not automatically permission to upload the whole research directory.
