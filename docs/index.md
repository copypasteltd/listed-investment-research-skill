# Documentation / 文档导航

[English README](../README.md) · [中文README](../README.zh-CN.md)

Start with installation and usage; load methodology and contracts when performing research. The agent-facing entry is [SKILL.md](../skills/ai-investment-research/SKILL.md), not this documentation index.

先安装并了解使用逻辑，再按研究任务读取方法和合同。智能体入口为 [SKILL.md](../skills/ai-investment-research/SKILL.md)。

| Topic / 主题 | English | 简体中文 |
|---|---|---|
| Setup and portability / 安装迁移 | [Installation](en/installation.md) | [安装](zh-CN/installation.md) |
| Workflow and commands / 使用流程 | [Usage](en/usage.md) | [使用逻辑](zh-CN/usage.md) |
| Research decisions / 研究方法 | [Methodology](en/methodology.md) | [方法论](zh-CN/methodology.md) |
| Modules and states / 系统组织 | [System logic](en/system-logic.md) | [系统逻辑](zh-CN/system-logic.md) |
| Evidence and schemas / 结构合同 | [Data contracts](en/data-contracts.md) | [数据合同](zh-CN/data-contracts.md) |
| Reader deliverables / 报告产物 | [Publishing](en/publishing.md) | [出版](zh-CN/publishing.md) |
| Review and limits / 质量边界 | [Quality](en/quality-and-limits.md) | [质量与限制](zh-CN/quality-and-limits.md) |
| Real output snapshots / 成品样本 | [Showcase](en/showcase.md) | [展示](zh-CN/showcase.md) |
| Troubleshooting / 排障 | [FAQ](en/faq.md) | [FAQ](zh-CN/faq.md) |

Additional references / 其他资料:

- [Synthetic offline demo / 合成离线演示](../examples/README.md)
- [Release validation / 本轮验收](validation.md)
- [Changelog / 更新记录](../CHANGELOG.md)
- [Contributing / 维护约定](../CONTRIBUTING.md)
- [Third-party notices / 上游声明](../THIRD_PARTY_NOTICES.md)
- [Publisher content contract / 出版内容合同](../skills/ai-investment-research/references/publisher_contract.md)
- [Pinned upstream hashes / 固定上游哈希](../skills/ai-investment-research/upstream-manifest.json)

## Choose a path / 选择入口

| Goal / 目标 | Entry / 入口 |
|---|---|
| Ask an agent for real research / 让智能体研究 | Install the Skill, invoke it with the security/cutoff/output location / 安装后给对象、截止和目录 |
| Verify the software without financial data / 无数据验证 | `python tools/demo.py --output /absolute/new-run` |
| Publish an already written report / 导出已有研究 | Core Markdown renderer or optional content-JSON publisher / MD导出或JSON出版 |
| Understand accounting and valuation constraints / 查会计估值规则 | Methodology + data contracts + quality / 方法、合同、质量 |
| Inspect examples / 看成品 | Showcase PDF and page images / 展示PDF与页面 |

The examples are historical or explicitly synthetic. The package has no unattended live-data, trading, or prediction-accuracy service. / 示例为历史或明确合成，本包没有无人值守实时数据、交易或命中率服务。
