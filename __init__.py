"""
GitHub PR Pipeline Parser

A tool to parse Tekton pipeline summaries from GitHub PR comments
and generate statistics about pipeline performance.
"""

__version__ = "1.0.0"
__author__ = "GitHub PR Pipeline Parser"
__email__ = "maintainer@example.com"

from .models import PipelineExecution, TaskExecution, TaskStatus, PipelineStatistics
from .parser import TektonPipelineParser
from .github_client import GitHubClient
from .stats_manager import StatisticsManager

__all__ = [
    'PipelineExecution',
    'TaskExecution',
    'TaskStatus',
    'PipelineStatistics',
    'TektonPipelineParser',
    'GitHubClient',
    'StatisticsManager'
]
