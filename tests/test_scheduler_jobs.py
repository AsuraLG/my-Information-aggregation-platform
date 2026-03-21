from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_collect_source_job_collects_only_target_source() -> None:
    from scheduler.jobs import collect_source_job

    source_a = MagicMock(id="source-a")
    source_b = MagicMock(id="source-b")
    sources_cfg = MagicMock(sources=[source_a, source_b])

    with patch("scheduler.jobs.load_sources", return_value=sources_cfg), \
         patch("collector.run_collection", return_value=[{"id": "raw-1"}]) as mock_run_collection, \
         patch("storage.convert_and_save", return_value=2) as mock_convert_and_save:
        collect_source_job("source-b")

    mock_run_collection.assert_called_once_with(source_b)
    mock_convert_and_save.assert_called_once_with([{"id": "raw-1"}], source_b)


def test_collect_source_job_returns_when_source_missing() -> None:
    from scheduler.jobs import collect_source_job

    sources_cfg = MagicMock(sources=[])

    with patch("scheduler.jobs.load_sources", return_value=sources_cfg), \
         patch("collector.run_collection") as mock_run_collection:
        collect_source_job("missing-source")

    mock_run_collection.assert_not_called()


def test_analyze_publish_job_uses_local_yesterday() -> None:
    from scheduler.jobs import analyze_publish_job

    with patch("scheduler.jobs.get_local_yesterday", return_value="2026-03-20"), \
         patch("analyzer.run_analysis", return_value=[]) as mock_run_analysis, \
         patch("publisher.render", return_value="output/index.html") as mock_render, \
         patch("publisher.deploy", return_value=True) as mock_deploy:
        analyze_publish_job()

    mock_run_analysis.assert_called_once_with("2026-03-20")
    mock_render.assert_called_once_with("2026-03-20")
    mock_deploy.assert_called_once_with()
