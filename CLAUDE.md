# 项目规范

## 包管理（重要）
- **必须使用 `uv` 管理所有依赖，禁止使用 `pip install`**
- 安装所有依赖：`uv sync`
- 添加新依赖：`uv add <package>`
- 运行脚本：`uv run python main.py`
- 运行测试：`uv run pytest`
- 不要直接执行 `python` 或 `pip`，始终通过 `uv run` 调用

## Python 环境
- Python 版本：3.9.6
- 所有 `.py` 文件顶部必须加 `from __future__ import annotations`
- 使用 `python` 命令（不用 `python3`）

## 代码风格
- 遵循 PEP 8，4 空格缩进
- 所有函数参数和返回值加类型注解
- 使用有意义的变量名和函数名
- 复杂逻辑添加注释

## 架构约定
- 各模块之间通过 `storage/` 的统一数据格式解耦，不直接互相调用
- 修改任何模块前，先阅读对应目录的 `AGENTS.md`
- 配置文件驱动：所有可变参数均在 `config/` 中定义，代码不硬编码业务参数

## 敏感信息
- API key 通过环境变量读取（`ANTHROPIC_API_KEY`），不写入任何配置文件
- `.env` 文件已加入 `.gitignore`，不提交到 git

## 测试
- 添加单元测试前需与用户确认
- 测试框架：pytest（通过 `uv run pytest` 执行）

## 作者信息
- author: ligen20
- 版权年份：2026
