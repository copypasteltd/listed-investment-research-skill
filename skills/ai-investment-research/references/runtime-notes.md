# Portable v1.1.0 运行说明

Python 3.10+。`research.py` 与 `install.py` 使用标准库；没有空的 core requirements。`run_macro.py` 与 vendor 中可选模块另有自身依赖与数据要求，按实际任务安装；不表示后台自动取数。

## 路径与状态

Agent 从用户简报和 [settings.json](../settings.json) 选择项目，默认当前项目的 `reports/日期_主题_唯一后缀/`；项目现有约定优先。`research.py init` 必须显式 `--output ABS_RUN_DIR`。`research.json` 记录模块状态，`sources.json`、`claims.json`、`forecasts.json` 记录证据、判断和预测。初始化不取数、不产生正文；`check --strict` 不联网、不证明事实。

原始数据在 `01_sources/raw/`，分析在 `02_analysis/`，模型和图表在 `03_models/`，正式阅读文件在 `04_deliverables/`，内部审计在 `99_internal/`。不把任何运行数据写回 skill。

## 依赖与字体

```text
python -m pip install -r "SKILL_ROOT/requirements-report.txt"
```

报告依赖为 ReportLab、PyMuPDF、Pillow，chartkit 另用 matplotlib、pandas、numpy。发布器优先 `--font-body PATH --font-head PATH`，其次 `AIR_FONT_BODY` / `AIR_FONT_HEAD`，再查系统字体。支持 ReportLab 可读的 TTF/TTC（TTC 默认 face 0）；不打包 Windows 字体。Windows 候选为现有 SimSun / Microsoft YaHei；Linux 候选为 Noto Serif/Sans CJK TTC，英文回退为 DejaVu。部分 Noto CJK TTC 是 CFF outline，ReportLab 不支持时会给错误，需改用具有授权的 TrueType CJK 字体；不会声称候选字体一定可用。

中文所需字形会在构建前检查；无合格字体明确失败。Linux 可先安装 `fonts-noto-cjk` 并检测兼容性，或通过参数提供 TrueType CJK 字体；英文 DejaVu 不能保证中文。HTML 使用本机字体栈，不嵌入字体；复制到其他机器仍需合格中文字体。

## 两条导出路径

- Markdown 主稿：`research.py render --run ABS_RUN_DIR --formats md,html,docx`。其兼容 `--formats html,pdf` 只尝试已安装浏览器，可返回 unavailable/failed；不下载浏览器。
- 默认严肃报告：按 [publisher_contract.md](publisher_contract.md) 写内容 JSON，再 `publisher.py --run ABS_RUN_DIR --content 99_internal/content.json`。可带上述字体参数。它离线生成同源 MD/HTML/PDF、manifest 与真实几何审计，不从 MD 猜 schema。重建会覆盖该 run 的同名成品，重要历史先使用新运行目录。

发布 status 的 pass / warning / fail 如实保留；warning 的 CLI 退出码仍是 0，必须读取 `warnings`。内容不安全、越界图片或字体不合格时返回 1，审计 fail 返回 2。目录真实起页迭代收敛，无法收敛失败；不写硬编码目录页码。

## Chartkit

```python
from chartkit import Charts
charts = Charts(run, font="/absolute/licensed-font.ttf")  # 或 AIR_CHART_FONT
charts.waterfall("bridge", ["a", "b", "total"], [2.0, -3.0, -1.0], "unit", "来源与适用期")
charts.price("weekly", csv_path, "来源与适用期", last="YYYY-MM-DD")
charts.finish()
```

调用方提供全部数据与图源，字体不合格时中文图表失败。`price` 的 `last` 是必填 keyword；只有有意不截断时传 `last=None`。瀑布桥接默认绝对容差 `1e-6`、相对容差 0；差 0.1 不能静默通过。确因展示值舍入需更宽容差时显式 `tolerance=...` 并解释口径，建议始终用未舍入输入。正负总值与堆叠方向保留真实符号。

## 跨平台安装

`--target` 是宿主的 **parent skills directory**，脚本自动从自身位置找到技能根：

```text
python "SKILL_ROOT/scripts/install.py" --target "HOST_SKILLS_DIR" --dry-run
python "SKILL_ROOT/scripts/install.py" --target "HOST_SKILLS_DIR" --mode copy
python "SKILL_ROOT/scripts/install.py" --target "HOST_SKILLS_DIR" --mode link --dry-run
```

默认 copy，包含 manifest 中隐藏上游文件，排除 Python 缓存。目标相同路径/相同内容时只读幂等；既有不同文件、目录或 junction 不覆盖、不重定向。link 在 POSIX 用 symlink，Windows 可用 symlink 或 junction；权限不足给出 copy 建议。默认不会发现或修改任何宿主安装位置。原 `install_local.ps1` 仅保留 Windows junction 兼容入口，使用时显式传目标并理解其参数；便携安装优先使用 Python 安装器。

## 验证

```text
python -B -m unittest discover -s "SKILL_ROOT/scripts" -p "test_*.py" -v
```

可设 `RESEARCH_TEST_TMPDIR` 到项目测试目录（测试根默认使用 OS temp）；测试均使用合成数据且自行清理，不获取真实证券数据。现有核心测试和新增发布器/安装器测试都不会改动原安装路径。
