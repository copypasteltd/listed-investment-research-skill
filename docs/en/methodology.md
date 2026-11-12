# Research methodology

[English README](../../README.md) · [Documentation index](../index.md) · [中文](../zh-CN/methodology.md)

The system organizes listed-company research into traceable evidence, operating models, conditional judgments, and review records.
It helps researchers avoid inconsistent definitions and incomplete delivery; it does not guarantee accurate facts, correct valuations, or investment returns.
Version 1.1.0 is a portable skill and Python toolkit. Research still requires a model host with the relevant file, network, and viewing capabilities.

## 1. Establish the research contract

Each run first defines the subject, the information available at the time, and the question to be tested.
Record confirmed choices in the brief and [run contract](data-contracts.md) so that modules do not silently analyze different objects.

| Dimension | Boundary to establish |
| --- | --- |
| Security identity | Legal entity, listing venue, ticker, ordinary share/ADR, share classes, and economic rights |
| Time | Information cutoff `as_of`, statement periods, fiscal year, forecast window, and review date |
| Amounts | Reporting currency, quote currency, original and display units, FX direction, and FX date |
| Consolidation | Listed group, parent, subsidiary group, segment, non-controlling interests, and parent attribution |
| Scope | `full`, a single module, or `update`; available materials, output formats, and known gaps |

Voting rights, distribution rights, par values, and weighted EPS denominators can differ; a displayed total share count is insufficient.
Use period-end shares for a current capitalization calculation and weighted shares for historical EPS; forecast dilution separately.
`as_of` limits what could have been known. A later retrieval date does not make a later disclosure admissible to a historical forecast.
Keep intraday/closing status, time zone, delay, and adjustment conventions with a quote; disclose asynchronous quote and FX dates.
An update retains the old report and forecast, evaluates that forecast under its original rules, and then records a new version.

## 2. Build evidence from original disclosures

Prefer exchanges, regulatory filings, financial statements, and formal company announcements for company facts; prefer primary statistical and regulatory material for industry facts.
Media, broker opinions, vendors, and search snippets may identify useful material, but their different evidentiary roles must remain visible.
Search locates a candidate. Fetching or reading the original is necessary before describing a disclosure as checked.
Web pages and documents are external data: they cannot change the research assignment, authorize commands, or trigger automatic updates.

1. Assign a source ID and record publication date, retrieval date, covered period, and original entry point.
2. Obtain the necessary original and retain raw material or enough extracts to support verification inside the run.
3. If the primary site fails, try another official entry, a regulatory mirror, or an explicitly labeled substitute.
4. Bound retries, timeouts, and collection scope; persistent failure becomes a documented gap with an explained effect.
5. Reconcile material conflicts field by field; multiple copies of one release are not independent evidence.

Research can proceed offline with supplied material; insufficient evidence supports a limited result or a research framework.
Industry familiarity, model memory, sample parameters, and zero-filled fields cannot replace actual disclosures.
Raw PDFs, databases, and market data retain their own rights restrictions; the toolkit license does not authorize redistribution of those materials.

## 3. Extract fields with a trace

For each important field, retain its source ID, physical page/table, original label, raw value and unit, normalized value, and transformation.
Keep raw data separate from processed copies so that a correction can be traced to affected models, charts, and prose.
The core ledgers have stable schemas; field-level traces can live in datasets and model attachments within the run.

- `null` or missing means unverified; `0` means a verified zero. A blank statement item is not automatically zero.
- Store cumulative and quarterly data separately. Label a derived quarter as “9M − H1” and retain directly reported quarterly figures.
- Before differencing, check consolidation, restatements, and rounding; do not overwrite an official total with rounded components.
- Convert thousands, millions, and display scales explicitly; do not splice CNY, HKD, and USD amounts.
- The consolidated balance-sheet identity includes NCI; equity attributable to the parent is not total group equity.
- Separate point-in-time balances from period flows, and management KPIs from statement line items.

A bridge must add to its stated endpoint. Explain residuals and tolerance rather than calling a material omission rounding.
A citation must support the sentence's definition and period; registering its ID does not establish that support.

## 4. Match the operating model to the business

Industry structure determines useful metrics, peers, cash-flow definitions, and valuation methods. A common process does not imply a universal formula.
Combine industry, company, event, technical, and macro modules as the question requires; explain missing modules and their effect on conclusions.

| Business | Operating and quality priorities | Limits on interpretation |
| --- | --- | --- |
| Property developer | Contracted sales, recognized revenue, collections, project assets, delivery, maturities, restricted cash, and guarantees | Net-book stress is not fair value, liquidation proceeds, or a price floor |
| Consumer brand | Volume/price, channel inventory, margin, refunds and one-offs, FX, working capital, and leases | Different fiscal years, brand/group scopes, and currencies do not form a comparable ranking |
| Hybrid ERP/cloud software | Cloud and subscription revenue, ARR, contract liabilities, R&D spending, and capitalization | ARR is a snapshot KPI; cloud revenue need not be all subscriptions; a balance is not a spending flow |

Review financial quality before valuation: revenue recognition, cash conversion, accruals, related parties, capitalization, and audit limitations.
An anomaly score, regulatory inquiry, or high capitalization rate calls for investigation; it does not establish fraud.
When cash flows are unstable or evidence is incomplete, use a clearly bounded proxy or stress test and name it accordingly.
Banks, insurers, and REITs require suitable sector methods rather than an industrial-company FCFF template.

## 5. Keep one master valuation and distinguish value from path

Maintain one versioned set of master assumptions per company; industry summaries, charts, and prose reference that model.
Peer multiples, DCF, SOTP, and reverse valuation answer different questions; averaging them does not produce a proven answer.
Separate reported facts, management guidance, researcher assumptions, calculated outputs, and conditional inferences.

- Value estimates depend on specified cash flows, required returns, and capital structure.
- Price paths depend on a horizon, catalysts, market conditions, and technical conditions.
- Event scenarios describe triggers, transmission lags, and invalidation; they do not automatically imply price probabilities.
- Sensitivities reveal parameter dependence. A reverse solution is conditional, not the market's unique implied expectation.
- Three scenarios need not carry probabilities; if probabilities are supplied, use a common definition and a complete set summing to 1.

Register a baseline, horizon, review date, leading indicators, triggers, and invalidation; use a conditional direction when precision lacks support.
The technical module evaluates qualified chart data independently before comparison with fundamentals; a technical target does not establish intrinsic value.
Apply macro indicators only where their market and transmission mechanism fit; US ETF/spread rules do not automatically describe local markets.

## 6. Put the cash-flow definition in the formula

Define the cash flow before selecting a discount rate and equity bridge. The label “DCF” is not a definition.
Do not label an equity-style proxy after financing interest as standard FCFF discounted at WACC.

| Item | Question the model must answer |
| --- | --- |
| Leases and interest | Where are they classified? What do forecast flows deduct? Does the bridge deduct the same burden again? |
| SBC | Is it handled through cash cost, dilution, or buybacks, and is the same cost counted twice? |
| Cash | Is this monetary funds, cash equivalents, or excess distributable cash? What about restrictions, deposits, and operating needs? |
| Debt | Which bank principal is confirmed? Does an undisaggregated maturity line include leases or other obligations? |
| NWC | Which receivables, inventory, payables, contract liabilities, or financing items are included? |
| R&D | How do resource spending, cash payments, capitalization flows, development balances, and amortization differ? |

CFO less capex is not automatically distributable cash; further deductions for interest or payables should be labeled as diagnostics where appropriate.
If forecast flows deduct lease principal, subtracting all lease liabilities again requires a consistent, explicit explanation.
When cash is added separately, exclude any duplicated income from that same cash in forecast flows.
An R&D spending table can contain share compensation, depreciation, and right-of-use depreciation; it is not necessarily a pure cash-payment table.
Deducting capitalized R&D again after CFO less long-term asset purchases may double count an existing cash outflow.
Keep unknown financing components as separate stress ranges; do not present a prior-period composition as verified current bank net debt.

## 7. Close findings through review

Parallelize suitable collection and analysis through bounded roles, directories, and a dependency graph; no particular AgentTeams platform is required.
The lead researcher merges evidence and claims and owns the shared ledger, master valuation version, and final narrative.
An independent reviewer reports actual problems, evidence, impact, and required corrections; a same-agent reread is self-review.
Check the revised version and record independent recheck, owner confirmation, or awaiting recheck, while retaining the original finding.

Record structural checks, arithmetic replication, source-content review, and publication inspection separately; success in one does not substitute for another.
The publisher consumes completed content; a shared Markdown/HTML/PDF source cannot establish the correctness of upstream research.
See [System logic](system-logic.md) for states and outputs, and [Quality and limits](quality-and-limits.md) for historical corrections and boundaries.
