from __future__ import annotations

from unittest.mock import MagicMock, patch


class DummyScheduler:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.jobs: list[dict] = []
        self.started = False

    def configure(self, **kwargs) -> None:
        self.kwargs.update(kwargs)

    def add_job(self, func, **kwargs) -> None:
        self.jobs.append({"func": func, **kwargs})

    def get_jobs(self) -> list[dict]:
        return self.jobs

    def start(self) -> None:
        self.started = True


def test_start_registers_per_source_jobs_with_isolated_executors() -> None:
    from scheduler.runner import start

    sources_cfg = MagicMock(
        sources=[
            MagicMock(id="rss_a", schedule="0 8 * * *"),
            MagicMock(id="rss_b", schedule="30 9 * * 1-5"),
        ]
    )
    schedule_cfg = MagicMock(timezone="Asia/Shanghai", analysis_schedule="15 10 * * *")
    dummy_scheduler = DummyScheduler()

    with patch("scheduler.runner.load_sources", return_value=sources_cfg), \
         patch("scheduler.runner.load_schedule", return_value=schedule_cfg), \
         patch("scheduler.runner.BlockingScheduler", return_value=dummy_scheduler) as mock_scheduler_cls, \
         patch("scheduler.runner.ThreadPoolExecutor", side_effect=lambda max_workers: {"max_workers": max_workers}):
        start()

    assert dummy_scheduler.started is True
    scheduler_kwargs = mock_scheduler_cls.call_args.kwargs
    assert scheduler_kwargs["timezone"].key == "Asia/Shanghai"
    assert scheduler_kwargs["executors"] == {
        "collect": {"max_workers": 4},
        "analyze_publish": {"max_workers": 1},
    }

    collect_jobs = [job for job in dummy_scheduler.jobs if job["id"].startswith("collect_")]
    assert len(collect_jobs) == 2
    assert collect_jobs[0]["args"] == ["rss_a"]
    assert collect_jobs[0]["executor"] == "collect"
    assert collect_jobs[0]["max_instances"] == 1
    assert collect_jobs[1]["args"] == ["rss_b"]
    assert collect_jobs[1]["day_of_week"] == "1-5"

    analyze_job = next(job for job in dummy_scheduler.jobs if job["id"] == "analyze_publish")
    assert analyze_job["executor"] == "analyze_publish"
    assert analyze_job["max_instances"] == 1
    assert analyze_job["minute"] == "15"
    assert analyze_job["hour"] == "10"


def test_start_skips_invalid_source_cron_and_invalid_analysis_cron() -> None:
    from scheduler.runner import start

    sources_cfg = MagicMock(sources=[MagicMock(id="broken", schedule="0 8 * *")])
    schedule_cfg = MagicMock(timezone="Asia/Shanghai", analysis_schedule="0 9 * *")
    dummy_scheduler = DummyScheduler()

    with patch("scheduler.runner.load_sources", return_value=sources_cfg), \
         patch("scheduler.runner.load_schedule", return_value=schedule_cfg), \
         patch("scheduler.runner.BlockingScheduler", return_value=dummy_scheduler), \
         patch("scheduler.runner.ThreadPoolExecutor", side_effect=lambda max_workers: {"max_workers": max_workers}):
        start()

    assert dummy_scheduler.started is True
    assert dummy_scheduler.jobs == []
