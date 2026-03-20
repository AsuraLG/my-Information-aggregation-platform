from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from config.loader import load_settings

logger = logging.getLogger(__name__)


def deploy(output_dir: Path | None = None) -> bool:
    """使用 ghp-import 将 output_dir 推送到 gh-pages 分支，返回是否成功"""
    settings = load_settings()

    if output_dir is None:
        output_dir = Path(settings.publish.output_dir)

    if not output_dir.exists():
        logger.error("输出目录不存在: %s", output_dir)
        return False

    remote = settings.publish.github_remote
    branch = settings.publish.github_branch

    cmd = [
        "ghp-import",
        "--no-jekyll",
        "--push",
        "--remote", remote,
        "--branch", branch,
        "--force",
        str(output_dir),
    ]

    logger.info("推送到 GitHub Pages: remote=%s branch=%s", remote, branch)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            logger.debug("ghp-import stdout: %s", result.stdout.strip())
        logger.info("GitHub Pages 部署成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("ghp-import 失败 (exit %d): %s", e.returncode, e.stderr.strip())
        return False
    except FileNotFoundError:
        logger.error("ghp-import 未安装，请运行: uv add ghp-import")
        return False
