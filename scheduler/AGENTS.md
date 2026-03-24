<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-03-19 | Updated: 2026-03-20 -->

# scheduler

## Purpose
调度模块，是整个系统的驱动引擎之一。按照 `config/schedule.yaml` 中定义的时间规则，定时触发采集任务和分析发布任务，确保整个闭环在无人干预下稳定重复执行。

> **注意**：本模块仅用于 APScheduler 模式（`main.py run`）。GitHub Actions 模式通过 `.github/workflows/*.yml` 独立调度，不经过本模块。两种调度方式互不影响。

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | 模块入口，暴露 `start()` 启动调度器 |
| `jobs.py` | 任务定义：`collect_source_job(source_id)` 和 `analyze_publish_job()`，分别封装单源采集和分析发布流程 |
| `runner.py` | 调度器主循环：加载配置，注册定时任务，启动并保持运行 |

## Subdirectories

_无子目录。_

## For AI Agents

### Working In This Directory
- `runner.py` 是系统的主入口，通过 `python -m scheduler` 或直接运行启动
- 采集任务和分析任务的调度时间独立配置，互不干扰
- 任务执行失败时只记录日志，不中断调度器本身（保证系统持续运行）
- 调度器重启后应能从配置重新加载任务，无需手动干预
- 建议使用 `APScheduler` 的 cron 触发器，与 `config/schedule.yaml` 中的 cron 表达式对应

### Testing Requirements
- **单元测试必须完善**，使用 `pytest`
- 调度逻辑本身较难单元测试，重点测试 `jobs.py` 中的任务函数
- 可通过手动触发 `collect_source_job()` / `analyze_publish_job()` 验证端到端流程

### Common Patterns
调度器启动约定：
```python
# scheduler/runner.py
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from zoneinfo import ZoneInfo

from config.loader import load_schedule, load_sources
from scheduler.jobs import collect_source_job, analyze_publish_job

def start():
    schedule = load_schedule()
    sources = load_sources()
    scheduler = BlockingScheduler(
        timezone=ZoneInfo(schedule.timezone),
        executors={
            "collect": ThreadPoolExecutor(max_workers=4),
            "analyze_publish": ThreadPoolExecutor(max_workers=1),
        },
    )  # 按 schedule.yaml 的 timezone 解释 cron，并隔离采集/分析发布执行器

    for source in sources.sources:
        scheduler.add_job(
            collect_source_job, 'cron',
            args=[source.id],
            executor="collect",
            max_instances=1,
            **parse_cron(source.schedule)
        )

    scheduler.add_job(
        analyze_publish_job, 'cron',
        executor="analyze_publish",
        max_instances=1,
        **parse_cron(schedule.analysis_schedule)
    )

    scheduler.start()
```

## Dependencies

### Internal
- `config/schedule.yaml` — 读取调度时间配置
- `collector/` — 调用采集入口
- `analyzer/` — 调用分析入口
- `publisher/` — 调用发布入口

### External
- `APScheduler` — 定时任务调度

<!-- MANUAL: Any manually added notes below this line are preserved on regeneration -->
