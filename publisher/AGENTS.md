<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# publisher

## Purpose
发布模块，负责将 `storage/` 中的摘要结果渲染为静态 HTML 页面，并自动推送到 GitHub Pages。支持按日期查看历史摘要，页面结构简洁，以内容可读性为优先。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `render(date: str)` 和 `deploy()` 两个独立接口 |
| `renderer.py` | 静态页面渲染器：读取摘要结果，构建 id→desc 映射，markdown→html 转换，使用 Jinja2 模板生成 HTML |
| `deployer.py` | GitHub Pages 部署器：将生成的静态文件推送到目标仓库的 gh-pages 分支 |
| `templates/` | Jinja2 HTML 模板目录 |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `templates/` | HTML 模板文件（index、daily summary、历史列表页） |

## For AI Agents

### Working In This Directory
- `render(date)` 生成指定日期的 HTML 页面，返回输出路径；`deploy()` 推送到 GitHub Pages
- 渲染时从 `config/tags.yaml` 和 `config/sources.yaml` 加载 id→desc 映射，展示时用 desc 替代 id
- AI 摘要为 markdown 格式，渲染时通过 `mistune.create_markdown(escape=True)` 转为 HTML
- 生成的静态文件输出到 `output/` 目录（已加入 `.gitignore`），再由 `deployer.py` 推送
- GitHub Pages 目标仓库和分支在 `config/settings.yaml` 中配置
- 部署失败时记录日志，不影响本地文件生成

### Testing Requirements
- **单元测试必须完善**，使用 `pytest`
- 渲染逻辑可用固定 fixture 数据测试，无需真实 AI 数据
- 部署步骤需可 mock（避免测试时真实推送）

### Common Patterns
发布流程约定：
```python
# publisher/__init__.py
def render(date: str) -> Path: ...
def deploy() -> bool: ...
```

模板目录结构：
```
templates/
└── index.html         # 首页（当日摘要，按标签分组展示）
```

## Dependencies

### Internal
- `storage/` — 读取 `SummaryResult`
- `config/settings.yaml` — 读取 GitHub Pages 仓库配置

### External
- `jinja2` — HTML 模板渲染
- `mistune>=3.0` — markdown → HTML 转换
- `ghp-import` — GitHub Pages 推送

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
