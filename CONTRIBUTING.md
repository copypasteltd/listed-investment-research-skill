# Contributing / 维护约定

[README](README.md) · [中文README](README.zh-CN.md)

## Scope / 范围

Prefer changes that improve evidence traceability, financial definitions, reproducibility, or agent usability. A copied checklist or additional fixed valuation model is not automatically an improvement. Keep the Skill entry short and route detailed guidance into focused references.

优先改进证据追溯、财务定义、可复算性和智能体可用性；不是新增清单或固定模型越多越好。入口保持精简，详细方法按需加载。

## Before proposing a change / 修改前

1. State the concrete research or publishing failure and its impact. / 说明实际问题及影响。
2. Preserve user scope, evidence cutoff, missing-value semantics and publication permissions. / 保留用户范围、截止、缺失语义和外发权限。
3. Do not commit credentials, user runs, proprietary fonts, or original paid/issuer datasets. / 不提交凭据、用户运行、版权字体或受限原始资料。
4. Keep pinned vendor files byte-identical. An upstream upgrade is a separate change with a new commit/hash inventory and license review. / vendor不改字节；升级另行固定与审查。
5. Use synthetic fixtures for tests. Do not turn a prior company example into a universal finance rule. / 测试使用合成数据，不将个股经验泛化成绝对规则。

## Verification / 验证

```bash
python -B -m unittest discover -s skills/ai-investment-research/scripts -p "test_*.py" -v
python tools/verify_repo.py
python tools/demo.py --output /absolute/path/to/new-synthetic-run
python tools/build_package.py --output dist
```

Optional publisher tests require report dependencies and compatible fonts. Record skipped capabilities and actual warnings. No test proves financial truth, visual quality, return, or forecast accuracy.

出版测试需要可选依赖和字体；记录实际跳过与提示。测试通过不证明事实、外观、收益或命中率。

## Documentation / 文档

Maintain English/Chinese parity for installation, commands, limits, and data contracts. Update both READMEs when a public CLI changes. Avoid machine-specific examples. If a fix changes a historical showcase, preserve its original hash and explain the published-copy edit.

安装、命令、边界和合同保持中英对应；CLI变化同步两份README。展示副本变化保留原哈希并说明，不改历史事实伪装新研究。

## Review and release / 复核发布

Separate author confirmation from independent revalidation. Review code, source hashes, docs links, package contents, and generated output before publishing. Never force-push or overwrite an unrelated host installation as a shortcut.

负责人确认与独立复验分开；发布前检查代码、源哈希、链接、包和真实导出。不强推历史、不覆盖无关安装。
