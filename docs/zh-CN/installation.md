# 安装与迁移

[文档导航](../index.md) · [English](../en/installation.md) · [使用逻辑](usage.md)

## 运行条件

| 能力 | 依赖 |
|---|---|
| 工作区、检查、MD/HTML/DOCX | Python 3.10+ 标准库 |
| 真实公司研究 | 宿主模型、文件/文档工具，以及相关一手资料访问能力 |
| 商务PDF出版 | 可选 `requirements-report.txt` 依赖及合法本地字体 |
| 数据制图 | 可选matplotlib、pandas、numpy；研究者提供真实数据 |
| 技术图形目视判断 | 如要声称完成，需图像模型或人工审阅 |
| 并行分析 | 宿主可选的子代理；单智能体也可分阶段完成 |

包中没有行情API密钥、模型账户或付费数据。上游独立工具可能有额外依赖和网络要求；`doctor` 只做诊断，不自动安装。

## 安装技能目录

在仓库根执行：

```bash
python skills/ai-investment-research/scripts/research.py doctor
python skills/ai-investment-research/scripts/install.py \
  --target /absolute/path/to/host/skills --mode copy --dry-run
python skills/ai-investment-research/scripts/install.py \
  --target /absolute/path/to/host/skills --mode copy
```

`--target` 是宿主的**技能父目录**，实际子目录为 `ai-investment-research`。默认复制模式独立于仓库；链接模式指向当前仓库，后续不能随意移动：

```bash
python skills/ai-investment-research/scripts/install.py \
  --target /absolute/path/to/host/skills --mode link
```

不同的既有Skill不会被覆盖。若已有其他版本，明确选择替代目录或自行安排迁移；安装器不删除、不强行替换目录或其他来源的junction。相同副本重复安装是否无操作，以实际返回结果为准，不能把无操作当成升级。

Codex通常使用配置的 `skills`，常见为 `~/.codex/skills`。其他宿主可能要求目录导入或刷新技能目录。复制成功并不证明宿主识别成功，应在对应宿主中调用 `$ai-investment-research`，确认入口可读。

## Windows

Python命令适用于PowerShell，路径要加引号。本文多行示例的 `\` 为Bash续行；PowerShell请放成单行或使用其反引号。

```powershell
python skills/ai-investment-research/scripts/install.py --target "$env:USERPROFILE/.codex/skills" --mode copy
```

链接可能受操作系统符号链接权限限制。保留的 [junction脚本](../../skills/ai-investment-research/scripts/install_local.ps1) 仅适用于Windows，无法推断DSH目录时必须显式指定；同样拒绝替换其他来源的既有入口。优先使用可迁移的Python安装器。

## PDF依赖和字体

建议在独立环境安装：

```bash
python -m venv .venv
# 按平台常规方式激活环境。
python -m pip install -r skills/ai-investment-research/requirements-report.txt
```

出版器支持 `--font-body`、`--font-head` 或环境变量 `AIR_FONT_BODY` / `AIR_FONT_HEAD`；Windows回退仅在对应本地字体存在时使用。Linux/macOS中文PDF请指定兼容的本地CJK TTF/TTC，不要假设西文字体支持中文。仅英文内容可选相应本地字体并核验实际产物。本包不分发版权系统字体。

```bash
python skills/ai-investment-research/scripts/publisher.py --help
```

若ReportLab无法嵌入某字体格式，应换用兼容字体，不静默把中文变成方框。字体可用、几何布局通过和目视验收是不同检查。

## 研究目录

公开设置不带私有绝对工作区。智能体可使用当前项目的 `reports/` 或用户显式目录。核心CLI仍要求 `--output` 为绝对路径；设置文件是给智能体的偏好，不是CLI隐式路径解析器。

安装资源与研究运行分开：不要向Skill安装目录写入用户财报、模型和成品，也不要把新研究运行提交到本仓库。

## 验证安装

```bash
python tools/demo.py --output /absolute/path/to/new-synthetic-run
python tools/verify_repo.py
```

前者离线使用明确合成数据；后者检查仓库封装与源完整性。二者均不证明实时取数、模型质量、金融事实或预测准确率。参见[质量与限制](quality-and-limits.md)。
