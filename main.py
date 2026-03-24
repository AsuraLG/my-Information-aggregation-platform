from __future__ import annotations

import argparse
import logging
import sys

# 统一日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def _today_local() -> str:
    from config.loader import get_local_today

    return get_local_today()


def _yesterday_local() -> str:
    from config.loader import get_local_yesterday

    return get_local_yesterday()


def cmd_collect(source_id: str | None = None) -> None:
    """手动触发采集"""
    from config.loader import load_sources
    import collector

    sources_cfg = load_sources()
    targets = sources_cfg.sources
    if source_id:
        targets = [s for s in targets if s.id == source_id]
        if not targets:
            logger.error("未找到信息源: %s", source_id)
            sys.exit(1)

    for src in targets:
        logger.info("开始采集: %s", src.id)
        items = collector.run_collection(src)
        if items:
            import storage
            new_count = storage.convert_and_save(items, src)
            logger.info("采集完成: %s，新增 %d 条", src.id, new_count)
        else:
            logger.warning("采集结果为空: %s", src.id)


def cmd_analyze(date: str | None = None) -> None:
    """手动触发分析"""
    import analyzer

    target_date = date or _yesterday_local()
    logger.info("开始分析: %s", target_date)
    results = analyzer.run_analysis(target_date)
    logger.info("分析完成，共生成 %d 条摘要", len(results))


def cmd_publish(date: str | None = None) -> None:
    """手动触发发布"""
    import publisher

    target_date = date or _yesterday_local()
    logger.info("开始发布: %s", target_date)
    output_path = publisher.render(target_date)
    logger.info("渲染完成: %s", output_path)
    success = publisher.deploy()
    if success:
        logger.info("发布完成")
    else:
        logger.error("发布失败")
        sys.exit(1)


def cmd_run() -> None:
    """启动调度器（长期运行）"""
    import scheduler

    logger.info("启动调度器...")
    scheduler.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="个人信息聚合平台")
    subparsers = parser.add_subparsers(dest="command")

    # collect
    p_collect = subparsers.add_parser("collect", help="手动触发采集")
    p_collect.add_argument("--source", help="指定信息源 id（不指定则采集全部）")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="手动触发分析")
    p_analyze.add_argument("--date", help="指定日期 YYYY-MM-DD（默认昨天）")

    # publish
    p_publish = subparsers.add_parser("publish", help="手动触发发布")
    p_publish.add_argument("--date", help="指定日期 YYYY-MM-DD（默认昨天）")

    # run
    subparsers.add_parser("run", help="启动调度器（长期运行）")

    args = parser.parse_args()

    if args.command == "collect":
        cmd_collect(getattr(args, "source", None))
    elif args.command == "analyze":
        cmd_analyze(getattr(args, "date", None))
    elif args.command == "publish":
        cmd_publish(getattr(args, "date", None))
    elif args.command == "run":
        cmd_run()
    else:
        # 无子命令时验证配置加载
        from config.loader import load_sources, load_schedule, load_prompts, load_settings, load_tags, validate_tags
        sources = load_sources()
        schedule = load_schedule()
        prompts = load_prompts()
        settings = load_settings()
        tags = load_tags()
        validate_tags(tags, sources)
        logger.info("配置加载成功：%d 个信息源", len(sources.sources))
        for src in sources.sources:
            logger.info("  - [%s] %s (tags: %s)", src.type, src.id, src.tags)
        logger.info("分析调度: %s", schedule.analysis_schedule)
        logger.info("AI 模型: %s", settings.ai.model)


if __name__ == "__main__":
    main()
