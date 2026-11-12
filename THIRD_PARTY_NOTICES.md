# Third-Party Notices / 第三方声明

This repository is an independent integration. It is not endorsed by upstream authors, issuers, exchanges, or data providers. / 本仓库为独立整合，不代表上游作者、上市公司、交易所或数据商背书。

## Pinned Skill methods / 固定上游方法

Five selected Skills from three repositories are bundled under the installable Skill’s `vendor/` directory. Original bytes, license texts and immutable source hashes are preserved. / 五个方法Skill来自三个固定提交仓库，原字节、许可证、来源与哈希均保留。

| Repository | Methods | Pinned commit | License |
|---|---|---|---|
| [anthropics/financial-services](https://github.com/anthropics/financial-services) | sector-overview | `60565064557ca77b12f62aa7877f365d111c129d` | [Apache-2.0](skills/ai-investment-research/vendor/anthropics-financial-services/LICENSE) |
| [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) | scenario-analyzer, technical-analyst, macro-regime-detector and support | `4251eaaeb05d720f5ffe8e899e3b6ec1cf48e96f` | [MIT](skills/ai-investment-research/vendor/tradermonty/LICENSE) |
| [rollingSirius/equity-research-skill](https://github.com/rollingSirius/equity-research-skill) | company research and valuation | `3d94e64ff53b325d866ea4bff69ad81a5adca8f5` | [MIT](skills/ai-investment-research/vendor/equity-research/LICENSE) |

The [complete manifest](skills/ai-investment-research/upstream-manifest.json) maps every retained upstream file to its original path, commit and hashes. The [Skill-level notices](skills/ai-investment-research/THIRD_PARTY_NOTICES.md) explain integration behavior. Integration changes live outside `vendor/`. No automatic upstream update is performed.

完整清单逐文件记录原路径、提交与哈希；整合改动在vendor外，包不会自动更新上游。

## Dependencies and data / 运行依赖与数据

Python dependencies are installed separately from their package registries and keep their respective licenses. They are not relicensed by this repository. In particular, optional PyMuPDF has its own licensing conditions; review its current license before embedding or redistributing a commercial product.

Python依赖需另行安装并保留各自许可证；本仓库不重新授权它们。可选PyMuPDF有独立许可条件，嵌入或再分发商业产品前应核对其当前许可。

The repository does not distribute model credentials, market-data subscriptions, proprietary fonts, or the original issuer filings used in research. Links to financial sources do not grant redistribution rights. Synthetic examples are labeled as such. Original report text and author-made charts are shown separately from underlying third-party evidence; see [showcase notices](showcase/NOTICE.md).

本仓库不分发模型凭据、行情订阅、版权系统字体或原始公司公告。来源链接不授予再分发权。合成示例有明确标记，报告文字/自制图表与底层第三方证据分别处理，详见展示声明。
