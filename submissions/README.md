# 提交插件

## 提交方式

1. Fork 本仓库
2. 复制 `TEMPLATE.json` → 重命名为 `{你的插件id}.json`
3. 填入信息，提交到 `submissions/` 目录
4. 向本仓库发 Pull Request

## 要求

- 插件 ID 使用小写字母、数字、下划线，1–32 位
- `manifest.json` 必须能通过面板校验（`api_version: 1`）
- `download_url` 必须是 **https**，且指向可直接下载的 zip
- 插件会经过自动风险扫描，含危险内容将被拒绝

## 审核

PR 会自动触发扫描，通过后由维护者合并。合并后自动进入 `index-community.json`。

社区插件**未经人工审核**，安装时面板会再次提示。