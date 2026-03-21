from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

from config.loader import load_sources, load_schedule
from scheduler.jobs import analyze_publish_job, collect_source_job

logger = logging.getLogger(__name__)

_COLLECT_EXECUTOR = "collect"
_ANALYZE_EXECUTOR = "analyze_publish"


def start() -> None:
    """配置并启动 BlockingScheduler，阻塞直到进程被终止"""
    sources_cfg = load_sources()
    schedule_cfg = load_schedule()

    scheduler = BlockingScheduler(
        timezone=ZoneInfo(schedule_cfg.timezone),
        executors={
            _COLLECT_EXECUTOR: ThreadPoolExecutor(max_workers=4),
            _ANALYZE_EXECUTOR: ThreadPoolExecutor(max_workers=1),
        },
    )

    # 为每个信息源注册独立的采集 cron job
    for src in sources_cfg.sources:
        cron_parts = src.schedule.split()
        if len(cron_parts) != 5:
            logger.warning("信息源 [%s] cron 表达式格式错误: %s，跳过", src.id, src.schedule)
            continue
        minute, hour, day, month, day_of_week = cron_parts
        scheduler.add_job(
            collect_source_job,
            trigger="cron",
            args=[src.id],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=f"collect_{src.id}",
            name=f"采集 {src.id}",
            executor=_COLLECT_EXECUTOR,
            max_instances=1,
            misfire_grace_time=300,
        )
        logger.info("注册采集任务 [%s]: %s", src.id, src.schedule)

    # 注册分析+发布 cron job
    analysis_cron = schedule_cfg.analysis_schedule.split()
    if len(analysis_cron) == 5:
        minute, hour, day, month, day_of_week = analysis_cron
        scheduler.add_job(
            analyze_publish_job,
            trigger="cron",
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id="analyze_publish",
            name="分析并发布",
            executor=_ANALYZE_EXECUTOR,
            max_instances=1,
            misfire_grace_time=600,
        )
        logger.info("注册分析发布任务 [%s]: %s", schedule_cfg.timezone, schedule_cfg.analysis_schedule)
    else:
        logger.error("analysis_schedule cron 格式错误: %s", schedule_cfg.analysis_schedule)

    logger.info("调度器启动，共 %d 个任务", len(scheduler.get_jobs()))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器已停止")
