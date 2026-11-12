# Data contracts and commands

[English README](../../README.md) · [Documentation index](../index.md) · [中文](../zh-CN/data-contracts.md)

This page describes the 1.1.0 research core and standalone publisher. All JSON is UTF-8 and field names are case-sensitive.
Examples use synthetic offline material, not real securities, current quotes, or actionable recommendations.
Run commands from the repository root. Replace `ABS_RUN_DIR`, `BODY_FONT`, and `HEAD_FONT` with the appropriate absolute paths.

## 1. Runs and paths

The [core script](../../skills/ai-investment-research/scripts/research.py) retains `schema_version: "1.0"`; product and schema versions are distinct.
Sources, claims, and forecasts are arrays of objects; run metadata is an object. IDs are unique within each ledger and retain their meaning.
`report_path`, module `artifact`, source `local_path`, and publication image paths are relative to the run and must resolve inside it.
Do not use traversal, drive letters, or symlinks to escape that boundary. CLI `--run`/`--output` arguments identify absolute directories.

| Contract | Root value and purpose |
| --- | --- |
| `research.json` | Object: research boundaries, module states, and delivery location |
| `sources.json` | Array: original evidence index |
| `claims.json` | Array: facts, calculations, assumptions, and judgments |
| `forecasts.json` | Array: trackable forecasts and subsequent reviews |
| `99_internal/content.json` | Object: completed content for the standalone publisher |

## 2. research.json

| Field | Type and rule |
| --- | --- |
| `schema_version` | String, fixed at `"1.0"` |
| `run_id`, `topic` | Nonempty strings; initialization generates a unique run ID and takes the topic from the task |
| `market` | `CN / HK / US / GLOBAL`; still identify each security's listing venue in cross-market work |
| `as_of` | `YYYY-MM-DD`, the information cutoff |
| `mode` | `full / industry / company / event / technical / macro / update` |
| `horizon` | Nonempty string describing the forecast window, not the historical lookback |
| `formats` | Nonempty array containing `md / html / docx / pdf` values |
| `companies` | Array of ticker/name strings; a company need not be specified |
| `created_at` | ISO date/time; initialization records actual UTC time |
| `report_path` | String, default `04_deliverables/report.md` |
| `status` | `draft / complete / limited` |
| `modules` | Object with five keys: `industry/company/event/technical/macro` |

Each module has the shape `{"status":"pending","reason":"","artifact":""}`.
States are `pending / complete / limited / skipped`; completed modules reference real artifacts, and limitations/skips explain their reason and effect.
In a full run, disclose unfinished modules in an actual report section titled `limitations` or its Chinese equivalent.
Put detailed share-class, currency, and accounting conventions in the brief and dataset; the core does not pretend to have dedicated required fields for all of them.

## 3. sources.json

Required strings are `id, title, publisher, url, published_at, retrieved_at, source_type, period`.
Optional `local_path` is run-relative, and optional `market` uses the market enum. Publication date is not the period covered.
`url` is an HTTP(S) original entry point, or a `local:` identifier with an existing `local_path`.
`published_at` is an ISO date/time; explicit `unknown` retains a warning and cannot establish availability at the cutoff.
`retrieved_at` is the real ISO date/time. Checks diagnose publication after retrieval, future retrieval, and look-ahead evidence.
`source_type` is a descriptive label such as `filing / regulator / statistics / company / data_vendor / news / user_material`, not a closed enum.

```json
[
  {"id":"S001","title":"SYNTHETIC OFFLINE EXAMPLE","publisher":"Demo author",
   "url":"local:synthetic-note","published_at":"2020-01-01","retrieved_at":"2020-01-02",
   "source_type":"user_material","period":"Synthetic FY2019",
   "local_path":"01_sources/raw/synthetic-note.txt","market":"GLOBAL"}
]
```

The referenced local file must exist. Local sources retain a warning that the network source has not been verified.

## 4. claims.json

| Field | Type and rule |
| --- | --- |
| `id`, `text` | Unique nonempty ID and nonempty claim text |
| `kind` | `fact / calculation / assumption / inference / scenario` |
| `source_ids` | Array of source-ID strings; facts and calculations need evidence |
| `as_of` | `YYYY-MM-DD`, the claim's information cutoff |
| `confidence` | `high / medium / low`: evidence strength, not event probability |
| `location` | Optional report-location description |
| `calculation` | Required for a calculation claim: a string describing formula, inputs, units, and model path |

Use citations such as `[S001]` in prose. Repeated citation of one source still represents one piece of evidence.
Datasets may hold field-level original labels, page/table references, units, and transformations; the core does not enforce one financial schema for these attachments.

## 5. forecasts.json

Required fields: `id, subject, forecast_type, as_of, horizon, baseline, leading_indicators, validation_date, status, source_ids`.
Optional fields: `target, unit, scenarios, realized_value, review_notes`; a reviewable forecast still needs explicit trigger and invalidation scenarios.

| Field | Type and rule |
| --- | --- |
| `id`, `subject`, `horizon` | Unique ID, forecast subject, and forecast window |
| `forecast_type` | `industry / fundamental / valuation / event / technical / macro` |
| `as_of`, `validation_date` | `YYYY-MM-DD`; validation cannot precede the forecast cutoff |
| `baseline` | Clear numeric or textual baseline with its observation date |
| `leading_indicators` | Nonempty array of observable signals |
| `status` | `open / realized / failed / partial / unverifiable` |
| `source_ids` | Array of registered source IDs |
| `target`, `unit` | Optional target and unit; distinguish operating quantity, value, and technical price |
| `scenarios` | Array of objects, each with nonempty `name, trigger, invalidation` strings |
| `probability` | Optional finite number inside each scenario, 0–1; if used, cover the complete set and sum to 1 |
| `realized_value`, `review_notes` | Observed outcome and review under the original rules |

Give new forecasts new IDs. Do not rewrite old targets, dates, or baselines to improve the record. Scenario probabilities are not historical hit rates.

## 6. Content JSON: the full publication input

The [publisher](../../skills/ai-investment-research/scripts/publisher.py) reads content; it does not derive or invent a report from the three evidence ledgers.
Required top-level strings are `title, subtitle, ticker, as_of, quote_note, judgment, filename`; explicitly supply empty strings where appropriate, but the safe filename must be nonempty.
`filename` is a filename or stem, optionally ending in `.pdf`; no directories, control characters, or Windows-invalid filename characters are allowed.
Optional `cover_metrics` contains at most three objects with string `value, label`; omit it or use an empty array when unnecessary.
`pages` is a nonempty array; each item has nonempty `section, title` strings and a `blocks` array.
A regular logical page may omit `type` or set it to `page`; a contents page uses `toc` and an empty `blocks` array.
YAML front matter is unnecessary. Skill-entry metadata is separate from this JSON; the publisher does not parse Markdown metadata to fill missing fields.

| block.type | Fields and constraints |
| --- | --- |
| `p`, `sub`, `note` | String `text`: paragraph, subheading, or note |
| `table` | Nonempty `headers` array and `rows` array; every row matches the header's column count |
| `table.widths` | Optional positive numeric array, one entry per column, summing to 1 within 0.001 |
| `chart` | Strings `path, title, source`; an existing run-local PNG/JPEG only |
| `source` | Six strings: `id, title, publisher, url, published_at, period`; URL is empty or HTTP(S) |

Inline text recognizes only `**bold**` and literal HTTP(S) URLs. HTML/XML is escaped as text rather than executed.
`[S...]` remains unchanged; the publisher neither establishes sentence-level support nor invents citation IDs or relationships.

```json
{
  "title":"Synthetic offline example","subtitle":"Not investment research","ticker":"DEMO",
  "as_of":"2020-01-01","quote_note":"No live quote","judgment":"Software demonstration only",
  "filename":"synthetic-example.pdf","cover_metrics":[],
  "pages":[
    {"type":"toc","section":"Navigation","title":"Contents","blocks":[]},
    {"section":"Example","title":"Explicit limits","blocks":[
      {"type":"p","text":"Synthetic content; no security recommendation."},
      {"type":"table","headers":["Field","Meaning"],"rows":[["null","Unverified"]],"widths":[0.3,0.7]}
    ]}
  ]
}
```

## 7. CLI and outputs

```text
python skills/ai-investment-research/scripts/research.py doctor
python skills/ai-investment-research/scripts/research.py init --output "ABS_RUN_DIR" --topic "Synthetic offline example" --market GLOBAL --as-of 2020-01-01 --mode company --format md,html,docx --company "DEMO Synthetic"
python skills/ai-investment-research/scripts/research.py check --run "ABS_RUN_DIR" --strict
python skills/ai-investment-research/scripts/research.py render --run "ABS_RUN_DIR" --formats md,html,docx
python skills/ai-investment-research/scripts/publisher.py --run "ABS_RUN_DIR" --content 99_internal/content.json --font-body "BODY_FONT" --font-head "HEAD_FONT"
```

`init` creates empty ledgers. Author the report and complete its records and states before checking/exporting; repeat `--company` for multiple companies.
Core formats are MD/HTML/DOCX/PDF; PDF needs an installed browser. The core downloads neither a browser nor research data.
Standalone PDF publication uses the [report dependencies](../../skills/ai-investment-research/requirements-report.txt). Supply fonts through flags or `AIR_FONT_BODY / AIR_FONT_HEAD`; installed Windows fonts provide a fallback.
The publisher writes `04_deliverables/{filename}.pdf`, `report.md`, `report.html`, and `99_internal/report_manifest.json`, `pdf-layout-audit.json`.
The manifest records input/output and image SHA256, fonts, planned/actual pages, logical-page spans, and actual section starts; the audit records real PDF text/image boxes, blank pages, bookmarks, and links.
`pass / warning / fail` return `0 / 0 / 2`; build exceptions return `1`. Overflow produces at least a warning, and contents use final pagination.
Core export separately writes `99_internal/check.json` and `delivery_manifest.json`; these are not aliases for standalone publisher audits.

Portable tools: `python tools/demo.py --output "ABS_RUN_DIR"` builds a synthetic offline example; `python tools/build_package.py --output dist` creates the skill archive; `python tools/verify_repo.py` checks static links, upstream hashes, and sensitive information.
Install with `python skills/ai-investment-research/scripts/install.py --target "PARENT_SKILLS_DIR" --mode copy --dry-run`, or use `--mode link`. The target is the parent skills directory; the installer does not overwrite an existing install or modify the host loader.
`check --strict`, repository verification, and publication audits do not establish factual truth, fair value, or forecast accuracy; see [Quality and limits](quality-and-limits.md).
