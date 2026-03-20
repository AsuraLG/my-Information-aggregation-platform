from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def collect_all_job() -> None:
    """采集所有信息源（由调度器调用）"""
    from config.loader import load_sources
    import collector
    import storage

    sources_cfg = load_sources()
    for src in sources_cfg.sources:
        try:
            items = collector.run_collection(src)
            if items:
                new_count = storage.convert_and_save(items, src)
                logger.info("采集完成 [%s]: 新增 %d 条", src.id, new_count)
            else:
                logger.warning("采集结果为空 [%s]", src.id)
        except Exception as e:
            logger.error("采集异常 [%s]: %s", src.id, e)


def analyze_publish_job() -> None:
    """分析并发布昨日数据（由调度器调用，顺序执行保证一致性）"""
    import analyzer
    import publisher

    date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info("开始分析发布流程: %s", date)

    try:
        results = analyzer.run_analysis(date)
        logger.info("分析完成: %d 条摘要", len(results))
    except Exception as e:
        logger.error("分析失败 [%s]: %s", date, e)
        return  # 分析失败则不发布

    try:
        output_path = publisher.render(date)
        logger.info("渲染完成: %s", output_path)
        success = publisher.deploy()
        if success:
            logger.info("发布完成 [%s]", date)
        else:
            logger.error("发布失败 [%s]", date)
    except Exception as e:
        logger.error("发布异常 [%s]: %s", date, e)
