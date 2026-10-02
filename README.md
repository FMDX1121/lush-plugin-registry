# 繁茂面板 · 插件仓库

官方与社区插件的中心索引。面板从 `index-official.json` 和 `index-community.json` 拉取。

## 清单

| 文件 | 内容 | 审核 |
|---|---|---|
| `index-official.json` | 官方/可信插件 | 人工审核 |
| `index-community.json` | 社区插件 | 自动扫描，未审核 |

## 安装方式

在面板「插件市场」中浏览并一键安装，或手动下载 zip 后通过面板上传。

## 提交插件

见 [`submissions/README.md`](submissions/README.md)。

## 风险扫描规则

所有提交的插件会经过 [`scripts/scan_risk.py`](scripts/scan_risk.py) 扫描：

- **危险** → 拒绝收录（`rm -rf /`、`curl | sh`、`mkfs` 等）
- **警告** → 收录但标记（使用 `subprocess`、`os.system`、`eval`、ELF 等）

## License

MIT
