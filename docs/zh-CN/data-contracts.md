# 数据契约与命令

[中文 README](../../README.zh-CN.md) · [文档索引](../index.md) · [English](../en/data-contracts.md)

本页描述 1.1.0 的研究核心及独立发布器。JSON 均为 UTF-8，字段名区分大小写。
下列例子为合成离线资料，不代表真实证券、当前报价或可交易结论。
命令从仓库根目录执行；`ABS_RUN_DIR`、`BODY_FONT`、`HEAD_FONT` 是需替换的绝对路径占位说明。

## 1. 运行与路径

[核心脚本](../../skills/ai-investment-research/scripts/research.py) 保持 `schema_version: "1.0"`；产品版本与 schema 版本不是同一个值。
来源、主张、预测各为对象数组；运行元数据为对象。ID 在各自账本内唯一并保持原义。
`report_path`、模块 `artifact`、来源 `local_path` 和发布图片路径相对于本次运行，解析后必须留在运行内。
不得用 `..`、盘符或符号链接把受约束路径导向运行外；CLI 的 `--run`/`--output` 则使用绝对目录。

| 契约 | 根值与作用 |
| --- | --- |
| `research.json` | 对象；研究边界、模块状态、交付位置 |
| `sources.json` | 数组；原始证据索引 |
| `claims.json` | 数组；事实、计算、假设与判断 |
| `forecasts.json` | 数组；可跟踪的前瞻与后续复盘 |
| `99_internal/content.json` | 对象；独立发布器的已完成内容输入 |

## 2. research.json

| 字段 | 类型及规则 |
| --- | --- |
| `schema_version` | 字符串，固定 `"1.0"` |
| `run_id`, `topic` | 非空字符串；初始化生成唯一运行 ID，主题由用户任务给定 |
| `market` | `CN / HK / US / GLOBAL`；跨市场证券仍逐项写清上市地 |
| `as_of` | `YYYY-MM-DD`，资料可知截止日 |
| `mode` | `full / industry / company / event / technical / macro / update` |
| `horizon` | 非空字符串；预测窗口，不是历史回看长度 |
| `formats` | 非空数组，值来自 `md / html / docx / pdf` |
| `companies` | 代码/名称字符串数组；允许没有指定公司 |
| `created_at` | ISO 日期/时刻；初始化记录真实 UTC 时刻 |
| `report_path` | 字符串，默认 `04_deliverables/report.md` |
| `status` | `draft / complete / limited` |
| `modules` | 对象，含 `industry/company/event/technical/macro` 五键 |

每个模块都是 `{"status":"pending","reason":"","artifact":""}` 形式的对象。
状态允许 `pending / complete / limited / skipped`；`complete` 指向真实产物，有限或跳过说明原因及影响。
完整范围的未完成模块须在正文的“资料缺口/局限”或 `limitations` 章节实际披露。
股类、报价币种、会计准则等详细口径写入简报和数据集，不假称核心已有独立必填字段。

## 3. sources.json

必填字符串为 `id, title, publisher, url, published_at, retrieved_at, source_type, period`。
可选 `local_path` 为运行内相对路径，`market` 为市场枚举；发布日与覆盖期间不能互换。
`url` 使用 HTTP(S) 原文入口，或 `local:` 标识并提供真实存在的 `local_path`。
`published_at` 用 ISO 日期/时刻；明确未知可写 `unknown`，保留警告，不能因此证明截止日当时已知。
`retrieved_at` 用真实 ISO 日期/时刻；发布晚于抓取、未来抓取及前视资料会被检查。
`source_type` 是实际类型标签，如 `filing / regulator / statistics / company / data_vendor / news / user_material`，并非封闭枚举。

```json
[
  {"id":"S001","title":"SYNTHETIC OFFLINE EXAMPLE","publisher":"Demo author",
   "url":"local:synthetic-note","published_at":"2020-01-01","retrieved_at":"2020-01-02",
   "source_type":"user_material","period":"Synthetic FY2019",
   "local_path":"01_sources/raw/synthetic-note.txt","market":"GLOBAL"}
]
```

此例需要先有对应本地文件；本地来源会保留“未核验网络来源”警告。

## 4. claims.json

| 字段 | 类型及规则 |
| --- | --- |
| `id`, `text` | 唯一非空 ID、非空主张文字 |
| `kind` | `fact / calculation / assumption / inference / scenario` |
| `source_ids` | 来源 ID 字符串数组；事实与计算须有来源 |
| `as_of` | `YYYY-MM-DD`，该主张的信息截止日 |
| `confidence` | `high / medium / low`；证据强弱，不是发生概率 |
| `location` | 可选，正文位置说明 |
| `calculation` | 计算主张需提供字符串，写公式、输入、单位和模型路径 |

正文使用 `[S001]` 等引用。一个来源多次被引用仍是一份证据。
逐字段 trace 可在数据集中保存原始标签、页表、单位和变换；这些附件没有被核心强制成统一财务 schema。

## 5. forecasts.json

必填：`id, subject, forecast_type, as_of, horizon, baseline, leading_indicators, validation_date, status, source_ids`。
可选：`target, unit, scenarios, realized_value, review_notes`；可复盘前瞻仍需明确触发与失效情景。

| 字段 | 类型及规则 |
| --- | --- |
| `id`, `subject`, `horizon` | 唯一 ID、预测对象、预测窗口 |
| `forecast_type` | `industry / fundamental / valuation / event / technical / macro` |
| `as_of`, `validation_date` | `YYYY-MM-DD`；验证日不得早于预测截止日 |
| `baseline` | 明确的数值或文字基准，并带观测时点 |
| `leading_indicators` | 可观察信号数组，不留空 |
| `status` | `open / realized / failed / partial / unverifiable` |
| `source_ids` | 已登记来源 ID 数组 |
| `target`, `unit` | 可选目标及单位；明确经营量、价值或技术价位 |
| `scenarios` | 对象数组；每项 `name, trigger, invalidation` 非空字符串 |
| `probability` | 情景内可选有限数值 0–1；一旦使用须覆盖整组并合计 1 |
| `realized_value`, `review_notes` | 到期实际结果及按原规则的复盘说明 |

新预测用新 ID；不回改旧目标、期限和基准来改善记录。情景概率不是历史命中率。

## 6. content JSON：完整出版输入

[发布器](../../skills/ai-investment-research/scripts/publisher.py) 只读取内容，不从三份账本推导或补造正文。
顶层必填字符串：`title, subtitle, ticker, as_of, quote_note, judgment, filename`；缺内容时显式空字符串，安全文件名必须非空。
`filename` 仅为文件名或 stem，可带 `.pdf`，不得含目录、控制字符或 Windows 非法文件名字符。
可选 `cover_metrics` 为最多三项的数组，每项含字符串 `value, label`；可以为空或省略。
`pages` 为非空数组，每项有非空 `section, title` 和 `blocks` 数组。
普通逻辑页可省略 `type` 或写 `page`；目录页写 `toc` 且 `blocks` 必须为空。
不需要 YAML front matter；技能入口自身的元数据不属于此 JSON 输入，发布器不解析 Markdown 元数据来补字段。

| block.type | 字段和约束 |
| --- | --- |
| `p`, `sub`, `note` | `text` 字符串；正文、小标题、注释 |
| `table` | 非空 `headers` 数组、`rows` 数组；每行列数与表头一致 |
| `table.widths` | 可选正数数组，长度等于列数，合计 1，容差 0.001 |
| `chart` | 字符串 `path, title, source`；仅运行内真实 PNG/JPEG |
| `source` | 六个字符串 `id, title, publisher, url, published_at, period`；URL 为空或 HTTP(S) |

正文仅识别 `**bold**` 与字面 HTTP(S) URL；HTML/XML 转义为文字，不执行任意标签。
`[S...]` 保留原样；发布器不验证它是否支持所在句，也不自动补编号或关系。

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

## 7. CLI 与输出

```text
python skills/ai-investment-research/scripts/research.py doctor
python skills/ai-investment-research/scripts/research.py init --output "ABS_RUN_DIR" --topic "Synthetic offline example" --market GLOBAL --as-of 2020-01-01 --mode company --format md,html,docx --company "DEMO Synthetic"
python skills/ai-investment-research/scripts/research.py check --run "ABS_RUN_DIR" --strict
python skills/ai-investment-research/scripts/research.py render --run "ABS_RUN_DIR" --formats md,html,docx
python skills/ai-investment-research/scripts/publisher.py --run "ABS_RUN_DIR" --content 99_internal/content.json --font-body "BODY_FONT" --font-head "HEAD_FONT"
```

`init` 只建空账本；先写真实报告、补齐记录和状态再检查/导出。重复 `--company` 可登记多家公司。
核心可用格式为 MD/HTML/DOCX/PDF，PDF 依赖已安装浏览器；不会自动下载浏览器或取数。
独立 PDF 发布安装 [报告依赖](../../skills/ai-investment-research/requirements-report.txt)，字体可用参数或 `AIR_FONT_BODY / AIR_FONT_HEAD` 指定，Windows 已有字体可作后备。
发布器输出 `04_deliverables/{filename}.pdf`、`report.md`、`report.html`，以及 `99_internal/report_manifest.json`、`pdf-layout-audit.json`。
manifest 记录输入/输出及图片 SHA256、字体、计划/实际页数、逻辑页起止和章节实际起页；audit 记录文字/图片框、空白页、书签与链接等真实 PDF 信息。
`pass / warning / fail` 分别返回 `0 / 0 / 2`；构建异常返回 `1`。长内容溢出至少警告，实际目录按最终分页生成。
核心导出另写 `99_internal/check.json` 与 `delivery_manifest.json`；这些不是独立发布器审计的别名。

便携工具命令：`python tools/demo.py --output "ABS_RUN_DIR"` 生成合成离线演示；`python tools/build_package.py --output dist` 生成技能包；`python tools/verify_repo.py` 检查静态链接、上游哈希与敏感信息。
安装器为 `python skills/ai-investment-research/scripts/install.py --target "PARENT_SKILLS_DIR" --mode copy --dry-run`，也支持 `--mode link`；目标为父 skills 目录，不覆盖既有安装或修改宿主加载器。
`check --strict`、仓库验证和发布审计都不证明事实、合理价值或预测准确；具体边界见 [质量与限制](quality-and-limits.md)。
