<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-19 -->

# publisher

## Purpose
发布模块，负责将 `storage/` 中的摘要结果渲染为静态 HTML 页面，并自动推送到 GitHub Pages。支持按日期查看历史摘要，页面结构简洁，以内容可读性为优先。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `run_publish(date: str)` 统一调用接口 |
| `renderer.py` | 静态页面渲染器：读取摘要结果，使用模板生成 HTML 文件 |
| `deployer.py` | GitHub Pages 部署器：将生成的静态文件推送到目标仓库的 gh-pages 分支 |
| `templates/` | Jinja2 HTML 模板目录 |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `templates/` | HTML 模板文件（index、daily summary、历史列表页） |

## For AI Agents

### Working In This Directory
- `run_publish(date)` 生成指定日期的页面并发布，通常在 `analyzer` 完成后由 `scheduler` 触发
- 生成的静态文件输出到 `output/` 目录（已加入 `.gitignore`），再由 `deployer.py` 推送
- GitHub Pages 目标仓库和分支在 `config/settings.yaml` 中配置
- 页面需包含：当日摘要（按标签分组）、历史日期导航
- 部署失败时记录日志，不影响本地文件生成

### Testing Requirements
- 渲染逻辑可用固定 fixture 数据测试，无需真实 AI 数据
- 部署步骤需可 mock（避免测试时真实推送）

### Common Patterns
发布流程约定：
```python
# publisher/__init__.py
def run_publish(date: str) -> None:
    summaries = storage.load_summaries(date)   # 读取摘要结果
    renderer.render(date, summaries)            # 生成 HTML 到 output/
    deployer.deploy()                           # 推送到 GitHub Pages
```

模板目录结构：
```
templates/
├── base.html          # 基础布局
├── index.html         # 首页（最新日期摘要）
├── daily.html         # 单日摘要页
└── archive.html       # 历史归档列表
```

## Dependencies

### Internal
- `storage/` — 读取 `SummaryResult`
- `config/settings.yaml` — 读取 GitHub Pages 仓库配置

### External
- `jinja2` — HTML 模板渲染
- `ghp-import` 或 `PyGithub` — GitHub Pages 推送
- `gitpython` — Git 操作（备选）

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
