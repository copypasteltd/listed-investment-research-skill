# 严肃商务报告发布器约定

实现：`publisher.py`。独立离线渲染，只读取已完成研究的 content JSON 与 run 内 PNG/JPEG；不联网、不补数据、不生成结论、不修改来源或图片。Python 环境需已有 reportlab、PyMuPDF（fitz）、Pillow。

## 调用与输出

```text
python "SKILL_ROOT/scripts/publisher.py" --run "ABS_RUN_DIR" --content "99_internal/content.json" --font-body "BODY_TTF_OR_TTC" --font-head "HEAD_TTF_OR_TTC"
```

`SKILL_ROOT` 解析为技能实际目录，portable 默认运行位于当前用户项目的 `reports/`（项目约定优先）。字体参数可省略以使用 `AIR_FONT_BODY` / `AIR_FONT_HEAD` 或系统候选，详见 [runtime-notes.md](runtime-notes.md)；本包不包含字体。

`--run` 必须是既有绝对目录，`--content` 必须相对于该目录。图片也必须是 run 内路径，解析后越界（包括符号链接越界）拒绝。

输出：

- `04_deliverables/{filename}.pdf`：filename 可含或不含 `.pdf`，不得含目录或 Windows 非法字符。
- `04_deliverables/report.md`：与 PDF 同源正文、表格、来源及目录实际 PDF 页码，图片相对于该 Markdown 所在目录引用。
- `04_deliverables/report.html`：与 PDF 同源内容，所有图像以原 PNG/JPEG 字节 data URI 嵌入，可单文件复制后离线阅读。使用本机字体栈，无外部脚本、样式、字体请求。
- `99_internal/report_manifest.json`：输入 SHA256、输出 SHA256/大小、图片 SHA256、字体、状态、planned/actual 页数、输入页实际起止页、section 实际起页。
- `99_internal/pdf-layout-audit.json`：真实 PDF 文本提取框、图片放置框和总数、中文提取、空白页、真实书签目标、可点击链接数、逐页统计、排版 flowable 实际区域。

同名输出可被重建覆盖；不删除、不移动输入或历史报告文件。审计 status=`pass`/`warning`/`fail`；CLI 分别返回 0/0/2。输入、字体或排版构建异常返回 1，并向 stderr 说明；构建异常时不要把任何既有 manifest 当成本次成功凭证。`warning` 是真实警告，主会话应读取并处理，不能当作严格通过。

## 固定 content schema

```json
{
  "title": "报告标题",
  "subtitle": "副标题",
  "ticker": "证券代码",
  "as_of": "资料基准日文本",
  "quote_note": "报价时点、币种及其他需要在封面说明的口径",
  "judgment": "研究者已经形成的判断文本",
  "filename": "报告文件名.pdf",
  "cover_metrics": [{"value": "已有数据文本", "label": "含单位口径的标签"}],
  "pages": [
    {"section": "章节名", "title": "该逻辑页标题", "blocks": [
      {"type": "p", "text": "正文，可使用 **加粗** 和引用[S001]"},
      {"type": "sub", "text": "小标题"},
      {"type": "note", "text": "来源、限定条件或注释"},
      {"type": "table", "headers": ["字段", "说明"], "rows": [["值", "说明文本"]], "widths": [0.3, 0.7]},
      {"type": "chart", "path": "03_models/charts/foo.png", "title": "图题", "source": "来源及适用期间"},
      {"type": "source", "id": "S001", "title": "来源标题", "publisher": "发布机构", "url": "https://example.com", "published_at": "发布日期", "period": "适用期间"}
    ]}
  ]
}
```

顶层上述文字字段必须为字符串，缺失应明确提供空字符串，不由排版器猜测。cover_metrics 可省略或为空，最多三项；每项必须有 value、label，数值仍由研究者提供。pages 必须非空，每页 section、title 必须为非空字符串，blocks 必须为数组。

table.widths 可省略，默认等宽；提供时长度必须等于列数、全部大于零、合计为 1（允许浮点误差 0.001）。rows 各行列数必须等于 headers；长表自动按行拆分，续页重复表头。单行过高无法容纳时构建明确失败，不缩小为难以阅读文字。

source 的六个字段均为字符串；无 URL 时写空字符串，否则只接受 HTTP(S)。原文 URL 在 PDF 和 HTML 中可点击。其他文字中的字面 HTTP(S) URL 也自动链接。正文只识别 `**bold**` 与字面 URL，其他 HTML/XML 作为文字转义；不执行 HTML、不接受任意 ReportLab 标签。`[S...]` 引用保留。Markdown 同样转义输入的 HTML 标签。引用与来源之间不补造编号或关系。

## 分页、目录与溢出

封面固定一页。正文每个输入 page 前显式 PageBreak；输入 page 中内容过多可真实拆成多页，不挤小正文、不伪造页码。planned_pages 恒为 1 + len(pages)，actual_pages 来自最终 PDF；不一致至少 warning，逐输入页 actual_start/actual_end 与 actual_page_count 将指出溢出来源。封面超过一页为 fail，应缩短封面标题、副标题、判断和说明。

目录可完全省略，PDF 仍有封面、section 和每个输入页标题的真实书签。需要可见目录时，在 pages 中加入以下页，blocks 为空：

```json
{"type":"toc", "section":"阅读导航", "title":"目录", "blocks":[]}
```

该扩展不改变普通页面 schema；普通页可不写 type，或写 `"type":"page"`。目录自动列出所有非 toc 输入页标题与真实 PDF 起页；最多六遍重新排版至起页映射收敛，无法收敛则明确失败。不要在 p/table 自写硬编码页码目录，排版器无法辨识研究者文字中的过期页码。

图宽 480pt，A4 正文宽约 499pt，落在 455–500pt 约定内；保持原图比例，图题/图片/图源作为整体放置，不裁切、不调色、不重新编码输入图。该整体若当前页放不下，会一起延至实际下一页，audit/manifest 会真实记录该逻辑页延页并 warning，后续目录重新计算。若原比例导致一页也放不下，明确拒绝，主会话应提供适合报告的横图，不能靠覆盖正文通过。

建议每个逻辑页使用一张横图及二至三段正文，或一张适度长度表格；这只是版面建议，不是内容限制。特别长 URL、长表单元格、长图等都以实际排版审计为准。

## 版式与审计边界

- A4 白纸黑字；正文 10pt / 16pt；标题采用独立 heading 字体。优先显式 TTF/TTC 参数或环境变量，再查系统候选：Windows 已有 SimSun/YaHei，Linux Noto Serif/Sans CJK TTC，英文可用 DejaVu。中文缺所需字形或 TTC 格式不兼容时给可操作错误，不以英文回退宣称中文正确；Windows 字体不随包再分发。
- 页边距左右 48pt；正文上界 66pt、下界距底 54pt；黑色页眉页脚，横向浅灰线。
- 表格白底、只有横向灰线；正文、注释、链接统一黑字。图表原色保留，配色由上游图表作者控制。
- 检查最终 PDF 中文可提取、正文文字/图片框不越过正文保留区域、空白正文页为零、图片放置总数等于输入 chart 数量、outline 目的地与最终真实起页一致。
- 图片数按实际放置次数计算；同一张图重复使用算多次。页眉页脚不算正文，不能用它们把空白页伪装成非空。
- 逐页 body_text_bounds 和 image_occurrences 提供可复核几何证据；审计不是 OCR，也不推断图像内部标签是否正确或研究事实是否成立。图中文字质量和源数据正确性仍由主会话核验。

## 已标注验证目录

`scripts/test_publisher.py` 在临时目录合成内容、图像与超长逻辑页，无真实证券研究。验证文字转义、路径限制、目录真实起页、中文字体检查、图像计数与 bounds、负值图表以及真实溢出 warning。测试自行清理，不把夹具、PDF、缓存或版权字体打包进技能。源项目三份报告的发布器由此封装保留，历史验证数据不是本包研究事实。
