# FAQ and troubleshooting

[Documentation](../index.md) · [中文](../zh-CN/faq.md)

## Does one command generate a live investment report?

No. `init` creates a run; `check` examines supplied records; the renderers export already written content. A host agent must obtain evidence, interpret disclosures, build the company-specific model, and write the analysis. The [offline demo](../../examples/README.md) uses fabricated data and proves only the software path.

## Do I need a particular model or search subscription?

No provider is hard-coded. You need a host with the capabilities the assignment actually requires. If search fails, direct official filings may still be accessible. If neither online sources nor user materials are available, the result must be a limited framework rather than invented real-company research.

## What remains after installing the Skill?

Host discovery, model credentials, data access and optional report dependencies remain your responsibility. `install.py` copies or links the folder without overwriting unrelated content. It does not modify account settings, enable plugins, or send research outside your machine.

## Why does the core require an absolute output path?

It prevents an ambiguous working directory from writing research into the installed Skill. Portable `settings.json` guides the agent; it is not an implicit path resolver in the CLI. Resolve the project and pass a new absolute run directory.

## Why is `check --strict` valid with warnings?

Some explicitly disclosed conditions remain warnings: an unknown publication date is not proof of point-in-time availability; a technical target does not prove fair value. Read the warnings. A valid structure is not certification that a document or conclusion is true.

## Can I use a technical target as an intrinsic value?

No. Completed-week price conditions, event scenarios and valuation assumptions have different meanings. Do not average them into a target or an upside probability. See [methodology](methodology.md).

## The company reports in one currency but trades in another. What changes?

Normalize the reporting currency and units first. Keep the quote currency, share class, economic share equivalence and FX date explicit. Period-end shares are not EPS weighted-average shares. A dated official FX reference must not be presented as synchronous spot FX.

## Can missing values be zero?

Only when the source establishes a zero. A blank debt cell, missing ARR, or unavailable subscription income is not automatically zero. A closing development balance is not current-period capitalized expenditure. Cumulative quarters need explicit differences to produce standalone quarters.

## PDF says `warning` and has more pages than planned. Is it broken?

Not necessarily. A long contents section or logical page can continue onto another actual page. The publisher reports the real mapping and bookmarks. Review the warning and geometry. A text/image bounds violation is different and must be repaired before claiming successful layout verification.

## Why does a font fail despite being installed?

The file may lack required Chinese glyphs or use outlines unsupported by ReportLab. Specify a compatible local TTF/TTC with the font arguments or environment variables. Do not assume that every Noto CJK collection embeds successfully. No proprietary fonts are bundled.

## Are chart images visually reviewed by the PDF audit?

No. It checks placement, hashes, counts, text and geometry. Chart data, labels, colors and interpretation require separate examination. If the current model cannot read images and no human checked them, say so.

## Is PDF the same as Word output?

The basic renderer creates DOCX from Markdown; the rich publisher creates PDF/HTML/Markdown from content JSON. They are separate routes with different layout capabilities. Do not run both over a finished report without preserving the authoritative source.

## Can I redistribute every file inside a research run?

No blanket right is implied. Issuer filings, market feeds, paid data, embedded fonts, user documents and credentials have separate rights and privacy constraints. The public showcase contains selected author-created report copies, not their original raw evidence.

## Does the report gallery prove returns or prediction accuracy?

No. It demonstrates historical research outputs, not an accuracy study. A performance claim needs a defined sample, cutoff, horizon, assessment rule and treatment of failed or unverifiable forecasts. Those results have not been established by this repository.

## How are upstream methods upgraded?

The bundled snapshot is pinned. Preserve vendor bytes and notices. A deliberate update needs a new upstream commit, source/hash inventory, compatibility checks and a clear explanation of changed behavior. No background auto-update is enabled.
