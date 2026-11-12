# Usage: from request to a reviewed report

[Documentation](../index.md) · [中文](../zh-CN/usage.md) · [Data contracts](data-contracts.md)

## 1. Give the agent a bounded assignment

Name the security, market, question, cutoff, output location, language, format, and useful horizon. The agent can infer routine defaults from the project; do not repeatedly request fields that are already known.

```text
Use $ai-investment-research for a full report on HKEX:09993.
Focus on asset realization, cash, debt and going-concern evidence.
Use only information available by the specified cutoff.
Produce a Chinese PDF under /absolute/project/reports/09993.
```

Use `company`, `industry`, `event`, `technical`, or `macro` for a scoped request. Use `update` for an existing report. A full report does not require a fabricated macro score or a technical target without suitable data.

## 2. Initialize a new run

```bash
python skills/ai-investment-research/scripts/research.py init \
  --output /absolute/project/reports/new-run \
  --topic "Company research" --market GLOBAL --as-of 2026-11-13 \
  --mode full --horizon "industry 3 years; company 18 months" \
  --format md,html,pdf --company "EXCHANGE:TICKER Company"
```

An existing valid run is returned for resumption without replacing its records. An unrelated existing directory is refused. Initialization creates no financial facts or report body.

## 3. Establish evidence before modeling

The host fetches documents with its available tools. Preserve sources and publication/retrieval times. For important numbers, keep the original unit, currency, period, group scope, page or table, conversion, and any unresolved conflict. Put raw material in `01_sources/` and normalized calculations in `03_models/`.

Useful primary routes include SEC filings and issuer IR for US securities, HKEXnews for Hong Kong issuers, exchange/CNINFO disclosures for China A-shares, and official statistics or peer disclosures for industry context. These are source strategies, not a guaranteed API connector list. A website may block a tool; an alternative official document can be used, but unavailable fields must remain missing.

## 4. Analyze independently, then integrate

Industry analysis defines the market and competitive denominator. Company analysis reconciles statements, operating KPIs and financial quality. Event work models a causal transmission path. Technical analysis uses eligible completed observations and remains separate from intrinsic value. Macro is included only when relevant to the security and geography.

If the host supports delegation, give contributors non-overlapping deliverables and source conventions. Retain one financial fact base and one main valuation model. No specific agent-team product is required. If only one agent worked, describe the review as self-review.

## 5. Write the ledgers and narrative

Update `sources.json`, `claims.json`, and `forecasts.json`; assign each relevant module a state and artifact. `full` describes the requested scope, not guaranteed completion. If a module is limited, disclose its name and effect in a `Limitations` / `资料缺口` section.

A decision-useful report includes the main judgment, strongest contrary evidence, accounting and business drivers, model assumptions, sensitivities, price conditions, validation dates, and the evidence gaps that would change the conclusion. Do not copy a prior report’s valuation or date into a new company.

## 6. Check and export

```bash
python skills/ai-investment-research/scripts/research.py check \
  --run /absolute/project/reports/new-run --strict
python skills/ai-investment-research/scripts/research.py render \
  --run /absolute/project/reports/new-run --formats md,html,docx
```

The source for this route is `04_deliverables/report.md`. For the richer PDF route, map the completed research to `99_internal/content.json`, run the [publisher](publishing.md), then inspect the final report and check the research ledgers again. Both routes can write the same report filenames: choose the authoritative narrative source deliberately instead of running competing exporters over finished outputs.

## 7. Review the actual files

Read the result, not only the exit code. For the publisher, `warning` may indicate a logical page overflow while the actual table of contents remains correct. Fix clipped text, absent charts, broken source paths, and unreadable fonts. Record visual review separately from machine geometry checks.

`check --strict` is not a truth engine. It does not reconstruct a value from every PDF or prove valuation consistency. Reconcile the material formulas and business assumptions independently.

## 8. Update without rewriting history

For an update, retain the original forecast IDs, baselines, dates, and assumptions. Evaluate past conditions first, mark realized/failed/partial/unverifiable as supported, and add new forecasts with new IDs. Archive older deliverables instead of making an old view appear to have known later facts.

## Supported and external responsibilities

| Task | In this package | Host/researcher responsibility |
|---|---|---|
| Run structure | Yes | Choose meaningful scope and cutoff |
| Source records and checks | Yes | Fetch and interpret actual source documents |
| Financial extraction | Guidance and traces | Extraction, reconciliation, and missing-data judgments |
| Valuation | Methods and retained calculator resources | Company-specific model and assumptions |
| PDF/HTML/Markdown | Optional publisher | Completed content and lawful local fonts |
| DOCX | Basic core renderer | Complex Office layout if required |
| Prediction accuracy | No | Only claim after a defined, auditable evaluation |
| Trading or publication | No default authorization | Separate explicit user instruction |
