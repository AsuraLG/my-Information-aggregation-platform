from __future__ import annotations

from types import SimpleNamespace
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, patch


class DummyScheduler:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.jobs: list[dict] = []
        self.started = False

    def add_job(self, func, trigger, **kwargs):
        self.jobs.append({"func": func, "trigger": trigger, **kwargs})

    def get_jobs(self):
        return self.jobs

    def start(self):
        self.started = True


def test_collect_source_job_only_collects_target_source() -> None:
    from config.loader import SourceConfig, SourcesConfig
    from scheduler.jobs import collect_source_job

    source_a = SourceConfig(id="src_a", type="rss", url="https://a.example.com/rss", tags=["AI"], schedule="0 9 * * *")
    source_b = SourceConfig(id="src_b", type="rss", url="https://b.example.com/rss", tags=["AI"], schedule="0 10 * * *")
    items = [{"id": "1"}]

    with patch("scheduler.jobs.load_sources", return_value=SourcesConfig(sources=[source_a, source_b])), \
         patch("collector.run_collection", return_value=items) as mock_collect, \
         patch("storage.convert_and_save", return_value=1) as mock_save:
        collect_source_job("src_b")

    mock_collect.assert_called_once_with(source_b)
    mock_save.assert_called_once_with(items, source_b)


def test_collect_source_job_skips_missing_source() -> None:
    from config.loader import SourcesConfig
    from scheduler.jobs import collect_source_job

    with patch("scheduler.jobs.load_sources", return_value=SourcesConfig(sources=[])), \
         patch("collector.run_collection") as mock_collect, \
         patch("storage.convert_and_save") as mock_save:
        collect_source_job("missing")

    mock_collect.assert_not_called()
    mock_save.assert_not_called()


def test_scheduler_registers_per_source_jobs_with_timezone_and_isolated_executors() -> None:
    from config.loader import SourceConfig, SourcesConfig
    from scheduler.jobs import analyze_publish_job, collect_source_job
    from scheduler.runner import start

    source_a = SourceConfig(id="src_a", type="rss", url="https://a.example.com/rss", tags=["AI"], schedule="0 9 * * *")
    source_b = SourceConfig(id="src_b", type="rss", url="https://b.example.com/rss", tags=["python"], schedule="15 10 * * *")
    sources_cfg = SourcesConfig(sources=[source_a, source_b])
    schedule_cfg = SimpleNamespace(timezone="Asia/Shanghai", analysis_schedule="0 20 * * *")
    created: list[DummyScheduler] = []

    def build_scheduler(**kwargs):
        scheduler = DummyScheduler(**kwargs)
        created.append(scheduler)
        return scheduler

    with patch("scheduler.runner.load_sources", return_value=sources_cfg), \
         patch("scheduler.runner.load_schedule", return_value=schedule_cfg), \
         patch("scheduler.runner.BlockingScheduler", side_effect=build_scheduler):
        start()

    scheduler = created[0]
    assert scheduler.started is True
    assert scheduler.kwargs["timezone"] == ZoneInfo("Asia/Shanghai")
    assert set(scheduler.kwargs["executors"].keys()) == {"collect", "analyze_publish"}

    collect_jobs = [job for job in scheduler.jobs if job["func"] is collect_source_job]
    assert len(collect_jobs) == 2
    assert collect_jobs[0]["args"] == ["src_a"]
    assert collect_jobs[0]["executor"] == "collect"
    assert collect_jobs[0]["max_instances"] == 1
    assert collect_jobs[1]["args"] == ["src_b"]
    assert collect_jobs[1]["executor"] == "collect"
    assert collect_jobs[1]["max_instances"] == 1

    analyze_jobs = [job for job in scheduler.jobs if job["func"] is analyze_publish_job]
    assert len(analyze_jobs) == 1
    assert analyze_jobs[0]["executor"] == "analyze_publish"
    assert analyze_jobs[0]["max_instances"] == 1
    assert analyze_jobs[0]["hour"] == "20"
