# Quality control and limits

[English README](../../README.md) · [Documentation index](../index.md) · [中文](../zh-CN/quality-and-limits.md)

The quality objective is inspectable evidence, transformations, assumptions, corrections, and artifacts, not a promise that research is always right.
Passing `check --strict` does not establish factual truth, fair value, forecasting skill, or suitability for trading.
The historical cases below come from project model/narrative review records dated 2026-11-13 and describe findings against particular versions.
They are neither continuously updated company views nor forecast validation, an audit opinion, or evidence of investment performance.

## 1. Different checks answer different questions

| Layer | What it can support | What it cannot support |
| --- | --- | --- |
| Source registration | An entry point, dates, period, and ID were recorded | The original is authentic/complete or the sentence cites it correctly |
| Structural check | Implemented rules for fields, enums, references, probabilities, paths, and gap disclosure are met | Every material defect has been found |
| Field-to-source check | A sampled field matches the source version read | Unsampled fields or later versions are also correct |
| Arithmetic replication | A specified formula reproduces from its inputs | The formula's economic meaning or assumptions are sound |
| Model review | Definition conflicts, double counting, and missing sensitivities can be identified | Exact spot fair value or a full independent audit |
| Publication audit | Actual pagination, text/image geometry, bookmarks, and links meet checks | Chart labels, source data, or research conclusions are correct |
| Visual inspection | Viewed pages have readable fonts, tables, charts, and pagination | Unviewed pages or every output format have passed |
| Forecast review | An original forecast has an outcome under its specified window and rules | An accuracy claim without a defined sample and methodology |

Strict core checking elevates some incomplete-record warnings to errors; it does not eliminate every warning.
Local material, unknown publication dates, and conditional technical targets can retain notices. Read the result rather than only its exit code.
Publisher `warning` also returns 0 and must not be described as an unqualified pass.

## 2. Property developer: three HK09993 model corrections

The historical model was a static net-book stress test. Its lack of a DCF target price was not itself a failure.
Review identified three concrete, fixable issues, and the subsequent final-report review independently closed those three.

| Finding | Correction and verification | General lesson |
| --- | --- | --- |
| A CFO bridge omitted CNY48.546 million | Added FX −29.135, receivable impairment +0.860, PPE disposal gain −4.512, finance income −0.959, and related-party payable decrease −14.800; the bridge then matched CFO of 1,215.276 | An omission equal to about 4% of CFO is not rounding |
| Two NCI allocations were labeled bounds | Relabeled as illustrative allocation scenarios, with outcomes potentially outside the range | Period-end parent/total equity proportions do not establish bounds on project-loss attribution |
| Negative parent book equity per share was floored at zero | Retained signed equity of −5,723.0686 million and approximately −HKD1.66844 per share | Negative book value is not a negative share-price forecast, and a zero floor is not a price floor |

Preserve passed checks too: conversions between thousands, millions, and display scales, parent-equity PB, and reference FX direction were reproducible.
CFO less interest and then excluding two payable increases was a diagnostic, not restated CFO, standard FCF, or proof of overdue payables.
A 3,954.443 million decline in short debt was not the same amount of cash repayment; gross debt declined only 94.990 million, requiring separate maturity analysis.
Existing impairment already reflected in net assets, guarantees, and pledged assets must not be mechanically added again as debt or losses.
A subsidiary group's September CAS figures cannot become the listed group's Q3 statements, and recognized revenue cannot fill missing contracted sales.

Later narrative review identified an unsupported collection-improvement claim, omitted intra-group components in assumed debt, unused maturity buckets, and two page-reference errors.
The record says the owner confirmed handling those items; it explicitly does not claim an independent reread of rebuilt artifacts or visual acceptance.
Accordingly, this page distinguishes independent closure of the first three from owner confirmation of the later four.

## 3. Consumer brand: ONON definitions and double-counting boundaries

The historical review confirmed that A/B distributions followed par value: economic A-equivalent shares were `A + B/10`.
302,025,490 A shares plus one tenth of 324,991,680 B shares equals 334,524,658 A-equivalent shares; total votes are not the valuation denominator.
Period-end economic shares, weighted EPS denominators, and forecast terminal dilution were treated separately.

- One-off refund: Q3 gross margin was approximately 72.6%, or 66.9% excluding CHF52.6 million. That one-sided adjustment was not the official two-sided normalized comparison.
- Historical FX: a 2021 field used pure FX losses of −16.3 while later years used net FX. It was corrected to approximately −14.9 with component traces retained.
- Profit bridge: an explicit rounding item changed from −0.1 to −0.2 CHF million so the disclosed one-decimal inputs reconciled to 371.0.
- Cash proxy: 9M CFO413.3 − capex84.6 − lease principal61.3 − cash interest20.2 = CHF247.2 million.
- Leases and SBC: once forecast cash deducted lease principal, the equity bridge did not subtract all lease liabilities again; explicit dilution avoided a second deduction for the same SBC cost.

The FX field and bridge rounding correction received independent reread closure; that did not turn the scenario DCF into exact spot fair value.
The intraday quote, earlier FX date, September cash, and year-end valuation anchor were asynchronous and needed disclosure.
Adding back all cash remained an assumption, not verified excess distributable cash; forecast flows also needed to exclude duplicate income on separately added cash.
NWC recomputed from rounded components differed by 0.1 from the company's published figures and needed separate labeling.
Final narrative review recorded planned clarifications for those last two points, not an independent reread of the text after those clarifications.

## 4. Hybrid ERP/cloud: Yonyou balances, flows, and cash

Historical review passed Q3 versus 9M−H1 differencing, units, and consolidated identities including NCI.
It also showed that correct arithmetic can coexist with a conflict between cash-flow and financing-bridge definitions.

| Pitfall | Treatment illustrated by this case |
| --- | --- |
| Cloud revenue equals subscriptions/ARR | Cloud revenue is a period flow; ARR and subscription contract liabilities are snapshot KPIs; management liabilities and consolidated current liabilities are distinct |
| Development balance equals capitalized spending | The 9M balance of 756.221310 million cannot automatically be 9M capitalized spending; retain an unavailable flow as `null` |
| R&D spending equals pure cash | FY2025 total spending of 2,427.070952 million includes share compensation and depreciation: resource/accrual spending, with cash payments requiring reconciliation |
| All intangible amortization equals R&D amortization | Total intangible amortization is not entirely internal R&D; do not invent a fully expensed profit adjustment from it |
| Debt service and bridge both deduct principal | Define flows after lease principal, financing interest, and ongoing R&D cash, but before bank principal; do not deduct leases again in the bridge |
| Mixed maturity liabilities are bank net debt | Treat undisaggregated current maturities as a separate uncertainty range rather than carrying H1 components forward as verified Q3 debt |

The revised main bridge was cash equivalents 1,608.665011 + trading financial assets 945.611823 − confirmed short borrowings 4,371.118398 = −1,816.841564 million.
Final narrative review confirmed that the new bridge and cash definition were synchronized, while short borrowings remained only a confirmed-debt floor and liquidity/operating-cash needs remained assumptions.
Monetary funds exceeded cash equivalents by 712.663241 million; that difference was not all proven restricted cash. Full add-back belonged in a separate sensitivity.
October financing proceeds cannot rewrite a September balance sheet; an H-share application is not completed fund-raising.
Later narrative review still required corrections to R&D “cash” wording and six chart-title/source descriptions that did not match plotted series.
Correct image counts and hashes therefore do not establish agreement between chart meaning, prose, and data.

## 5. Record correction closure

1. Preserve the reviewed version, specific evidence, severity, and actual effect on the conclusion.
2. Correct the mapping, formula, or definition, then synchronize model outputs, charts, and prose.
3. Recompute or reread the revised version and state the scope of that recheck.
4. Record independent recheck, owner confirmation, awaiting recheck, or a continuing limitation; retain the original finding and rationale.
5. Rebuild publication and read this build's manifest/audit. Old success records cannot override a new failure.

A reviewer without visual input should state that no visual inspection occurred; reading plotting code is not viewing the image.
One agent adopting several roles performs self-review, not an independent review.
Limit corrections to problems supported by evidence rather than counting an already disclosed limitation as a new error.

## 6. Publication, examples, and use boundaries

Synthetic offline examples are a first-class entry point for learning directories, contracts, checking, and publishing without live quotes or vendor credentials.
Historical published cases are frozen snapshots, not current company facts; later disclosures, prices, and corporate actions require fresh verification.
Pinned upstream files retain their licenses and hashes. Upgrades require renewed provenance checks, not execution of upstream auto-update or external-send instructions.
Raw filing PDFs, market databases, third-party charts, and paid materials retain their own licenses; an open code repository must not automatically redistribute them.

The system does not guarantee complete market, disclosure, or risk coverage. Offline evidence, network failures, sampling, and unverified dates constrain conclusions.
Proxy cash flows, terminal assumptions, required returns, cash availability, and dilution can dominate value; show sensitivities instead of false precision.
Do not claim model accuracy without a defined sample, window, original forecasts, protection against hindsight changes, and assessment rules.
Research authorization does not include orders, fund movements, account changes, or automatic external publication; those require separate explicit user authorization.
At delivery, preserve the cutoff, limited modules, unfinished checks, and material assumptions so readers can assess the conditions under which a conclusion holds.
