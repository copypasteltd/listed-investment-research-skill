# Examples / 示例

[English README](../README.md) · [中文README](../README.zh-CN.md)

## Offline synthetic run / 离线合成运行

```bash
python tools/demo.py --output /absolute/path/to/new-synthetic-run
```

Run from the repository root. The output directory must not exist. No live data, API, LLM, browser, or financial credential is used; the core path needs only Python 3.10+.

从仓库根运行，输出目录必须为尚不存在的绝对路径；没有真实行情、网络API、模型调用或金融凭据，基础路径仅需Python标准库。

The generator writes all of the following using **fabricated** numbers:

- Research scope and source/claim/forecast ledgers.
- Raw fixture values in `01_sources/raw/synthetic.json`.
- A small analysis artifact and Markdown report.
- Strict-check evidence and an independent HTML export.

生成内容包括研究合同、三份台账、合成原始数、分析与正文、严格检查及HTML。所有数字明确标注虚构，不能用于研究事实或预测统计。

## Optional PDF / 可选PDF

```bash
python -m pip install -r skills/ai-investment-research/requirements-report.txt
python tools/demo.py --output /absolute/path/to/new-synthetic-pdf --pdf \
  --font-body /absolute/path/to/cjk-body.ttf \
  --font-head /absolute/path/to/cjk-heading.ttf
```

The PDF fixture includes a locally drawn synthetic chart, Chinese text, a table, sources, and limitations. Its HTML embeds the image. The generated audit checks actual pages, text extraction, images, and geometry; it is not a visual-design review.

PDF含本地绘制的合成图、中文、表格、来源与限制，HTML内嵌图片。验收只证明文件、文字、图片和几何结构，不冒充目视设计审阅。

## Real report snapshots / 历史真实成品

The three examples in [showcase](../docs/en/showcase.md) are separate, dated historical outputs. They are not the offline demo and are not generated from its synthetic numbers. Original issuer documents and internal research runs are not included.

[三份案例](../docs/zh-CN/showcase.md) 是独立的历史研究快照，不由本合成示例生成；不附原始公司公告或内部运行目录。复制报告外观不代表可以复制其日期或数值作为新研究。
