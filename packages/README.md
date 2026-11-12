# Installable package / 可安装分发包

[Repository README](../README.md) · [中文README](../README.zh-CN.md)

- [ai-investment-research-v1.1.0.zip](ai-investment-research-v1.1.0.zip)
- [File inventory and SHA-256](ai-investment-research-v1.1.0.manifest.json)
- [SHA256SUMS](SHA256SUMS)

The archive contains the complete `ai-investment-research/` Skill folder, including references, helpers, tests, pinned vendor snapshots, manifests and licenses. It excludes repository-level documentation, showcase PDFs, raw research runs, credentials, environments, and proprietary fonts.

ZIP包含完整技能目录、方法引用、脚本、测试、固定上游、清单和许可证；不含仓库级文档、展示PDF、研究原件、凭据、环境或版权字体。

Extract into a new directory and use `ai-investment-research/scripts/install.py` to install into an explicit host skills directory. Existing unrelated installations are not replaced. Check the SHA-256 before using a downloaded archive.

解压到新目录后，使用包内安装器指定宿主技能父目录；不会替换不同的既有安装。下载后先核对SHA-256。

```bash
python tools/build_package.py --output dist
```

The builder produces the same archive bytes from the same Skill files: sorted paths, fixed ZIP timestamps and per-file hashes. Changes to the Skill require rebuilding and updating the checksum/inventory; rebuilding documentation alone does not modify the Skill archive.

相同技能输入以路径排序、固定ZIP时间戳和逐文件哈希生成同字节归档；修改技能后须重新生成包和清单，仅文档变化不改变技能归档。
