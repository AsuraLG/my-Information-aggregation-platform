from __future__ import annotations

import logging

from config.loader import get_local_yesterday, load_sources

logger = logging.getLogger(__name__)


def collect_source_job(source_id: str) -> None:
    """采集单个信息源（由调度器调用）"""
    import collector
    import storage

    sources_cfg = load_sources()
    source = next((src for src in sources_cfg.sources if src.id == source_id), None)
    if source is None:
        logger.error("未找到信息源 [%s]，跳过本次采集", source_id)
        return

    try:
        items = collector.run_collection(source)
        if items:
            new_count = storage.convert_and_save(items, source)
            logger.info("采集完成 [%s]: 新增 %d 条", source.id, new_count)
        else:
            logger.warning("采集结果为空 [%s]", source.id)
    except Exception as e:
        logger.error("采集异常 [%s]: %s", source.id, e)


def analyze_publish_job() -> None:
    """分析并发布昨日数据（由调度器调用，顺序执行保证一致性）"""
    import analyzer
    import publisher

    date = get_local_yesterday()
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
