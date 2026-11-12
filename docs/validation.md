# Release validation / 本轮验收

[README](../README.md) · [中文README](../README.zh-CN.md)

This page records validation performed for the 1.1.0 public package. Historical report production checks are described separately in the showcase manifest. Software tests do not prove financial truth or investment performance.

本页记录1.1.0公开包的真实验收；历史报告检查另见展示清单。软件测试不证明金融事实或投资表现。

## Executed checks / 已执行检查

| Check / 项目 | Result / 结果 | Boundary / 边界 |
|---|---|---|
| Skill frontmatter and naming / 技能元数据 | Passed `quick_validate.py` / 已通过 | Does not evaluate investment reasoning / 不评价投资判断 |
| Core / installer / publisher / chart tests / 核心、安装、出版、图表 | **44 tests passed, zero skips / 44项通过、无跳过** | Python3.13 Windows local execution / 本机实际运行 |
| Synthetic core demo / 合成基础演示 | Created run, strict check valid, MD/HTML exported / 通过 | No network/model/live values / 无网络模型和真实数据 |
| Synthetic rich PDF / 合成商务PDF | Exported with explicit local CJK fonts / 已导出 | No proprietary fonts bundled / 不附字体文件 |
| Vendor inventory / 上游清单 | 111 pinned files across 3 repositories / 111份、3仓库 | Hash comparison, not upstream quality endorsement / 仅哈希核对 |
| Public report snapshots / 展示报告 | 40/46/43 pages, 24/26/28 figures, 30/33/30 source IDs / 数量已核 | Historical snapshots not reverified against live issuers / 未重新实时取证 |
| Preview generation / 页面展示 | Real PDF rasterization, no AI-generated illustrations / 真实PDF渲染 | Geometry/nonblank checks, no full visual review / 未完整目视验收 |

## Test environment and reproducible commands / 环境与复现

Local verification uses Python 3.13 on Windows with installed report dependencies and local CJK fonts. CI is configured for Windows and Ubuntu with Python 3.10/3.13. **Configured CI is not evidence that remote jobs have already succeeded.** Read the actual Actions results after publication. A missing compatible CJK font can produce an explicit test skip on an environment without such a font; that is not a verified Chinese PDF.

本机为Windows/Python3.13，已有可选出版依赖与本地CJK字体；CI配置覆盖Windows/Ubuntu与Python3.10/3.13。**已配置不代表远端已执行通过**，发布后以Actions实际结果为准。缺兼容CJK字体时相应测试可明确跳过，不能因此宣称中文出版已验。

```bash
python -B -m unittest discover -s skills/ai-investment-research/scripts -p "test_*.py" -v
python tools/verify_repo.py
python tools/demo.py --output /absolute/path/to/new-synthetic-run
python tools/demo.py --output /absolute/path/to/new-synthetic-pdf --pdf \
  --font-body /local/body.ttf --font-head /local/heading.ttf
python tools/build_package.py --output dist
```

Test temporary roots must be outside the installed Skill when testing its CLI installer. An initial local run encountered the installer's correct nested-target rejection because its fixture root was inside the source; the fixture was corrected and all 44 tests were rerun successfully without relaxing the installer boundary.

安装器CLI测试的临时根必须位于源Skill外。本轮首次全量运行因测试临时目录处于源内而被正确拒绝，已调整夹具位置，未放宽安装器保护。

## Final local verification / 最终本地验收

- **44 tests passed with zero skips**: 22 core, 14 publisher/chart, 8 installer tests. / 44项通过，无跳过。
- Skill metadata validation passed. Synthetic core export and a three-page Chinese PDF demo were executed successfully. / 元数据、合成核心导出及三页中文PDF已实际运行通过。
- Authored local documentation links, 111 pinned vendor files and seven showcase PDF/image hashes passed offline verification. / 自有文档链接、111份固定上游及7个展示文件哈希通过。
- Independent repository review found no blocking publication issue. Its identified showcase-hash schema mismatch was corrected and the seven-file verification rerun. / 独立仓库复核无阻断项，展示哈希结构映射遗漏已修复并重验。
- The archive was extracted and all 141 files were hashed again. `doctor`, `init` and `install` ran with Python `-S` (site packages disabled); repeated copy installation returned `already-installed`. / 解压回读141文件，禁用site包仍可诊断/初始化/安装，重复安装只读幂等。
- Package: [v1.1.0 ZIP](../packages/ai-investment-research-v1.1.0.zip), 649,287 bytes, 141 files. SHA-256: `b4316eb63b618f47160798c18b912ad4fdab8c8c58c7542587b277ec26482298`.

This is local validation. Remote Actions execution is separate and must be read from its actual results. No credentials, private workspace paths or raw research-session logs are published. / 以上为本地验收，远端Actions须看实际结果；不发布凭据、私有路径或会话日志。
