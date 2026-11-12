# 使用逻辑：从请求到经过复核的报告

[文档导航](../index.md) · [English](../en/usage.md) · [数据合同](data-contracts.md)

## 1. 给智能体明确的研究任务

指定证券、市场、研究问题、截止日、目录、语言、格式与期限。常规默认可由项目推断，已明确的字段不反复询问。

```text
使用 $ai-investment-research 对 HKEX:09993 进行完整研究。
重点是资产实现、现金、债务和持续经营证据。
只用截止日前实际可知的信息，在 /absolute/project/reports/09993 交付中文PDF。
```

专项可使用 `company`、`industry`、`event`、`technical`、`macro`；更新使用 `update`。完整研究不意味着必须编一个宏观分数，也不意味着无合格行情仍要给技术目标。

## 2. 初始化研究运行

```bash
python skills/ai-investment-research/scripts/research.py init \
  --output /absolute/project/reports/new-run \
  --topic "公司研究" --market GLOBAL --as-of 2026-11-13 \
  --mode full --horizon "行业3年；公司18个月" \
  --format md,html,pdf --company "EXCHANGE:TICKER 公司"
```

已有合法运行会原样返回供继续，不覆盖其记录；普通已存在目录被拒绝。初始化不会生成公司事实或研报正文。

## 3. 先取证，再建模

由宿主工具抓取实际文档，记录来源、发布时间与取数时间。重要数字保留原始单位、币种、期间、合并范围、页码/表格、转换公式和未解决冲突。原件放 `01_sources/`，标准化数据与计算放 `03_models/`。

常用一手路径包括美股SEC及公司IR、港股HKEXnews、A股交易所/巨潮、行业官方统计及同业正式披露。它们是资料策略，不是承诺全部可达的API连接器。某工具被站点拒绝时可寻找同一事实的其他官方原文，缺数仍保留缺失。

## 4. 各模块独立形成判断，再综合

行业明确分母与竞争；公司复算三表、经营KPI和质量；事件建立因果传导；技术只使用合格已完成观测并与内在价值分列；宏观仅在适用市场且确实相关时加入。

宿主有子代理时，明确不重叠的交付范围及来源约定；共享事实和主估值只维护一份。不依赖特定AgentTeams产品。单智能体完成时如实标自审，不冒称独立复核。

## 5. 完成台账与报告

维护 `sources.json`、`claims.json`、`forecasts.json`，并给适用模块写状态与产物。`full`表示请求范围，不保证全部完成。有限模块在“资料缺口/Limitations”章节说明模块名、原因及结论影响。

有用的报告包括主判断、最强反方、经营与会计驱动、估值假设、敏感性、价格条件、验证日期及会改变结论的缺口。不把旧报告的日期、折现率和目标套到另一家公司。

## 6. 校验与导出

```bash
python skills/ai-investment-research/scripts/research.py check \
  --run /absolute/project/reports/new-run --strict
python skills/ai-investment-research/scripts/research.py render \
  --run /absolute/project/reports/new-run --formats md,html,docx
```

这条路线使用 `04_deliverables/report.md`。商务PDF路线先把完整研究映射为 `99_internal/content.json`，运行[出版器](publishing.md)，检查成品后再检查台账。两条路线可能写相同文件名，必须明确哪份内容是主源，不要对最终成品重复运行不同导出器造成覆盖。

## 7. 检查真实文件

读取产物而不是只看退出码。出版器 `warning` 可能仅为逻辑页自然延展，实际目录依然正确；文本被裁切、图表缺失、来源路径无效或字体不可读则需要修复。目视验收与几何检查分别记录。

`check --strict` 不会从每份PDF重新恢复全部数字，也不证明估值一致。重要公式和商业假设必须另行复算。

## 8. 更新时不改写历史

保留原预测ID、基准、日期和假设；先按原条件评估，到期后据证据标记实现、失败、部分或无法验证，再新增新ID预测。旧成品归档，不把当时观点伪装成已经知道后来事件。

## 工具与宿主的责任边界

| 任务 | 包内支持 | 宿主/研究者负责 |
|---|---|---|
| 运行结构 | 有 | 合理对象、问题和截止 |
| 来源与结构检查 | 有 | 抓取并读取原始证据 |
| 财务提取 | 方法与溯源约定 | 抽取、复算和缺数处理 |
| 估值 | 方法及保留的计算资源 | 公司具体模型与假设 |
| PDF/HTML/MD | 可选出版器 | 已完成内容及合法字体 |
| DOCX | 基础导出 | 复杂Office布局 |
| 预测准确率 | 不提供 | 仅在定义清楚的可审计评估后声称 |
| 交易或外部发布 | 无默认授权 | 另行用户明确指令 |
