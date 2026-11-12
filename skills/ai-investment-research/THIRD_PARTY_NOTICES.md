# Third-Party Notices

This package integrates research methods from five selected Skills in three upstream repositories. Upstream files in `vendor/` are byte-preserved snapshots, including their copyright and license notices. The integration instructions and original helper scripts outside `vendor/` are licensed under the root MIT LICENSE.

| Upstream | Components | Pinned commit | Applicable license |
| --- | --- | --- | --- |
| [Anthropic financial-services](https://github.com/anthropics/financial-services) | sector-overview | 60565064557ca77b12f62aa7877f365d111c129d | [Apache License 2.0](vendor/anthropics-financial-services/LICENSE) |
| [TraderMonty claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) | scenario-analyzer, technical-analyst, macro-regime-detector; supporting agent and shared files | 4251eaaeb05d720f5ffe8e899e3b6ec1cf48e96f | [MIT](vendor/tradermonty/LICENSE), Copyright (c) 2026 TraderMonty |
| [rollingSirius equity-research-skill](https://github.com/rollingSirius/equity-research-skill) | equity-research and repository resources | 3d94e64ff53b325d866ea4bff69ad81a5adca8f5 | [MIT](vendor/equity-research/LICENSE), Copyright (c) 2026 Sirius |

No root NOTICE file was found in the selected repository trees at acquisition. The complete file mapping, upstream paths, immutable URLs and hashes are recorded in [upstream-manifest.json](upstream-manifest.json).

## Integration changes

The wrapper and references unify module selection, market scope, language, output paths, evidence and forecast records, review, and delivery. They replace independent upstream orchestration and format/confirmation defaults when running this integration. Source snapshots themselves are unmodified. This is an independent integration, not an official joint product or endorsement by any upstream author, company, analyst, or data provider.

Source-code licenses do not grant financial-data subscriptions, model credentials, API quotas, data redistribution rights, or rights to third-party materials referenced by upstream examples. Preserve source attribution and applicable license texts when redistributing the package. Do not treat example reports or author-supplied performance claims as newly verified research.
