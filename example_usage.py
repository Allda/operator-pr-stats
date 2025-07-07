#!/usr/bin/env python3
"""
Example usage script for GitHub PR Pipeline Parser

This script demonstrates how to use the library programmatically
to parse pipeline summaries and generate statistics.
"""

import os
import sys
from datetime import datetime
from github_client import GitHubClient
from parser import TektonPipelineParser
from stats_manager import StatisticsManager
from models import TaskStatus


def main():
    """Main example function"""
    print("🚀 GitHub PR Pipeline Parser - Example Usage")
    print("=" * 50)

    # Check if GitHub token is available
    if not os.getenv('GITHUB_TOKEN'):
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub token:")
        print("export GITHUB_TOKEN=your_token_here")
        return 1

    # Initialize components
    print("📡 Initializing components...")
    try:
        github_client = GitHubClient()
        parser = TektonPipelineParser()
        stats_manager = StatisticsManager("example_data")
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        return 1

    # Example 1: Test parser with sample comment
    print("\n🧪 Example 1: Testing parser with sample comment")
    print("-" * 40)

    sample_comment = """
# Pipeline Summary

Pipeline: `example-tekton-pipeline`
Success Rate: 75.0%
Duration: 12m 45s

## Task Status
- fetch-source: ✅ (1m 20s)
- build-image: ✅ (3m 45s)
- run-tests: ❌ (test failure)
- security-scan: ✅ (2m 15s)
- deploy: ⏭️ (skipped due to test failure)
"""

    execution = parser.parse_pipeline_summary(
        sample_comment,
        pr_number=123,
        pr_url="https://github.com/example/repo/pull/123",
        repository="example/repo"
    )

    if execution:
        print(f"✅ Parsed pipeline: {execution.name}")
        print(f"   Status: {execution.status.value}")
        print(f"   Success Rate: {execution.success_rate}%")
        print(f"   Tasks: {execution.successful_tasks}/{execution.total_tasks}")

        # Add to statistics
        stats_manager.add_execution(execution)
        print("📊 Added to statistics database")
    else:
        print("❌ Failed to parse sample comment")

    # Example 2: Demonstrate statistics features
    print("\n📈 Example 2: Statistics demonstration")
    print("-" * 40)

    # Add a few more sample executions
    sample_executions = [
        {
            "comment": """
# Pipeline Summary
Pipeline: `example-tekton-pipeline`
Success Rate: 100.0%
- fetch-source: ✅
- build-image: ✅
- run-tests: ✅
- security-scan: ✅
- deploy: ✅
""",
            "pr_number": 124,
            "status": "success"
        },
        {
            "comment": """
# Pipeline Summary
Pipeline: `another-pipeline`
Success Rate: 50.0%
- compile: ✅
- test: ❌
""",
            "pr_number": 125,
            "status": "failed"
        }
    ]

    for i, sample in enumerate(sample_executions):
        execution = parser.parse_pipeline_summary(
            sample["comment"],
            pr_number=sample["pr_number"],
            pr_url=f"https://github.com/example/repo/pull/{sample['pr_number']}",
            repository="example/repo"
        )
        if execution:
            stats_manager.add_execution(execution)
            print(f"✅ Added execution {i+1}: {execution.name}")

    # Show summary statistics
    print("\n📊 Summary Statistics:")
    stats_manager.print_summary()

    # Show detailed pipeline statistics
    print("\n🔧 Pipeline Details:")
    stats_manager.print_pipeline_stats()

    # Example 3: Export statistics
    print("\n💾 Example 3: Export statistics")
    print("-" * 40)

    export_file = stats_manager.export_to_json("example_export.json")
    if export_file:
        print(f"✅ Statistics exported to: {export_file}")

    # Example 4: Query specific data
    print("\n🔍 Example 4: Query specific data")
    print("-" * 40)

    # Get failed executions
    failed_executions = stats_manager.get_executions(status=TaskStatus.FAILED)
    print(f"❌ Found {len(failed_executions)} failed executions")

    # Get executions for specific pipeline
    pipeline_executions = stats_manager.get_executions(pipeline_name="example-tekton-pipeline")
    print(f"🔧 Found {len(pipeline_executions)} executions for 'example-tekton-pipeline'")

    # Get recent executions
    recent_executions = stats_manager.get_executions(limit=3)
    print(f"🕐 {len(recent_executions)} most recent executions:")
    for exec in recent_executions:
        print(f"   - {exec.name} ({exec.status.value}) - {exec.parsed_at.strftime('%Y-%m-%d %H:%M')}")

    print("\n🎉 Example completed successfully!")
    print("Check the 'example_data' directory for generated files.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
