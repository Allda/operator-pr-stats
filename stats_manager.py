"""
Statistics manager for pipeline execution data
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from models import (
    PipelineExecution, PipelineStatistics, StatisticsDatabase,
    TaskStatus, TaskExecution
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class StatisticsManager:
    """Manages pipeline statistics and persistence"""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize statistics manager

        Args:
            data_dir: Directory to store statistics data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.db_file = self.data_dir / "pipeline_stats.json"
        self.console = Console()

        # Load existing data
        self.database = self._load_database()

    def _load_database(self) -> StatisticsDatabase:
        """Load statistics database from file"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    return StatisticsDatabase(**data)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not load existing database: {e}[/yellow]")
                self.console.print("[yellow]Starting with empty database[/yellow]")

        return StatisticsDatabase()

    def _save_database(self) -> None:
        """Save statistics database to file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.database.model_dump(), f, indent=2, default=str)
        except Exception as e:
            self.console.print(f"[red]Error saving database: {e}[/red]")

    def add_execution(self, execution: PipelineExecution) -> None:
        """Add a new pipeline execution to the database"""
        # Add to executions list
        self.database.executions.append(execution)
        self.database.total_executions += 1

        # Add repository if not already tracked
        if execution.repository and execution.repository not in self.database.repositories:
            self.database.repositories.append(execution.repository)

        # Update pipeline statistics
        self._update_pipeline_stats(execution)

        # Update last updated timestamp
        self.database.last_updated = datetime.now()

        # Save to file
        self._save_database()

    def add_executions(self, executions: List[PipelineExecution]) -> None:
        """Add multiple pipeline executions"""
        for execution in executions:
            self._add_execution_without_save(execution)

        # Save once at the end
        self._save_database()

    def _add_execution_without_save(self, execution: PipelineExecution) -> None:
        """Add a pipeline execution without saving to file"""
        # Add to executions list
        self.database.executions.append(execution)
        self.database.total_executions += 1

        # Add repository if not already tracked
        if execution.repository and execution.repository not in self.database.repositories:
            self.database.repositories.append(execution.repository)

        # Update pipeline statistics
        self._update_pipeline_stats(execution)

        # Update last updated timestamp
        self.database.last_updated = datetime.now()

    def _update_pipeline_stats(self, execution: PipelineExecution) -> None:
        """Update aggregated statistics for a pipeline"""
        pipeline_name = execution.name

        # Get or create pipeline statistics
        if pipeline_name not in self.database.pipelines:
            self.database.pipelines[pipeline_name] = PipelineStatistics(name=pipeline_name)

        stats = self.database.pipelines[pipeline_name]

        # Update execution counts
        stats.total_executions += 1
        if execution.status == TaskStatus.SUCCESS:
            stats.successful_executions += 1
        elif execution.status == TaskStatus.FAILED:
            stats.failed_executions += 1

        # Update success rate
        if stats.total_executions > 0:
            stats.success_rate = (stats.successful_executions / stats.total_executions) * 100

        # Update dates
        if not stats.first_seen or execution.parsed_at < stats.first_seen:
            stats.first_seen = execution.parsed_at
        if not stats.last_seen or execution.parsed_at > stats.last_seen:
            stats.last_seen = execution.parsed_at

        # Update repositories
        if execution.repository and execution.repository not in stats.repositories:
            stats.repositories.append(execution.repository)

        # Update task statistics
        self._update_task_stats(stats, execution.tasks)

    def _update_task_stats(self, pipeline_stats: PipelineStatistics, tasks: List[TaskExecution]) -> None:
        """Update task-level statistics"""
        for task in tasks:
            task_name = task.name

            if task_name not in pipeline_stats.task_statistics:
                pipeline_stats.task_statistics[task_name] = {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'skipped_executions': 0,
                    'success_rate': 0.0
                }

            task_stats = pipeline_stats.task_statistics[task_name]
            task_stats['total_executions'] += 1

            if task.status == TaskStatus.SUCCESS:
                task_stats['successful_executions'] += 1
            elif task.status == TaskStatus.FAILED:
                task_stats['failed_executions'] += 1
            elif task.status == TaskStatus.SKIPPED:
                task_stats['skipped_executions'] += 1

            # Update success rate
            if task_stats['total_executions'] > 0:
                task_stats['success_rate'] = (task_stats['successful_executions'] / task_stats['total_executions']) * 100

    def get_pipeline_stats(self, pipeline_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific pipeline or all pipelines"""
        if pipeline_name:
            if pipeline_name in self.database.pipelines:
                return self.database.pipelines[pipeline_name].model_dump()
            else:
                return {}

        return {name: stats.model_dump() for name, stats in self.database.pipelines.items()}

    def get_executions(self, pipeline_name: Optional[str] = None,
                      repository: Optional[str] = None,
                      status: Optional[TaskStatus] = None,
                      limit: Optional[int] = None) -> List[PipelineExecution]:
        """Get filtered pipeline executions"""
        executions = self.database.executions

        # Apply filters
        if pipeline_name:
            executions = [e for e in executions if e.name == pipeline_name]

        if repository:
            executions = [e for e in executions if e.repository == repository]

        if status:
            executions = [e for e in executions if e.status == status]

        # Sort by parsed_at (newest first)
        executions.sort(key=lambda x: x.parsed_at, reverse=True)

        # Apply limit
        if limit:
            executions = executions[:limit]

        return executions

    def get_summary(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get overall summary statistics with optional filtering"""

        # Get filtered executions
        filtered_executions = self._apply_execution_filters(self.database.executions, filters or {})

        # Get filtered pipelines
        filtered_pipelines = self._apply_pipeline_filters(self.database.pipelines, filters or {})

        total_pipelines = len(filtered_pipelines)
        total_executions = len(filtered_executions)
        total_repositories = len(set(e.repository for e in filtered_executions if e.repository))

        successful_executions = sum(1 for e in filtered_executions if e.status == TaskStatus.SUCCESS)
        failed_executions = sum(1 for e in filtered_executions if e.status == TaskStatus.FAILED)

        overall_success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

        return {
            'total_pipelines': total_pipelines,
            'total_executions': total_executions,
            'total_repositories': total_repositories,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'overall_success_rate': overall_success_rate,
            'last_updated': self.database.last_updated,
            'repositories': list(set(e.repository for e in filtered_executions if e.repository)),
            'filtered': bool(filters)
        }

    def _apply_execution_filters(self, executions: List[PipelineExecution], filters: Dict[str, Any]) -> List[PipelineExecution]:
        """Apply filters to execution list"""
        filtered = executions

        if 'repository' in filters:
            filtered = [e for e in filtered if e.repository == filters['repository']]

        if 'status' in filters:
            filtered = [e for e in filtered if e.status == filters['status']]

        return filtered

    def _apply_pipeline_filters(self, pipelines: Dict[str, PipelineStatistics], filters: Dict[str, Any]) -> Dict[str, PipelineStatistics]:
        """Apply filters to pipeline statistics"""
        filtered = {}

        for name, stats in pipelines.items():
            # Check minimum executions filter
            if 'min_executions' in filters and stats.total_executions < filters['min_executions']:
                continue

            # Check repository filter
            if 'repository' in filters:
                if filters['repository'] not in stats.repositories:
                    continue

            # If we get here, pipeline passes all filters
            filtered[name] = stats

        return filtered

    def print_summary(self, filters: Optional[Dict[str, Any]] = None) -> None:
        """Print formatted summary to console with optional filtering"""
        summary = self.get_summary(filters)

        # Create summary table
        title = "Pipeline Statistics Summary"
        if summary.get('filtered', False):
            title += " (Filtered)"

        table = Table(title=title)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Pipelines", str(summary['total_pipelines']))
        table.add_row("Total Executions", str(summary['total_executions']))
        table.add_row("Total Repositories", str(summary['total_repositories']))
        table.add_row("Successful Executions", str(summary['successful_executions']))
        table.add_row("Failed Executions", str(summary['failed_executions']))
        table.add_row("Overall Success Rate", f"{summary['overall_success_rate']:.1f}%")
        table.add_row("Last Updated", str(summary['last_updated']))

        self.console.print(Panel(table, title="📊 Statistics Summary", expand=False))

    def print_pipeline_stats(self, pipeline_name: Optional[str] = None, show_tasks: bool = False, filters: Optional[Dict[str, Any]] = None) -> None:
        """Print pipeline statistics to console with optional filtering"""
        if pipeline_name:
            # Single pipeline details with potential filtering
            stats = self.get_pipeline_stats(pipeline_name)
            if stats:
                # Apply execution-level filtering for single pipeline
                pipeline_executions = self.get_executions(pipeline_name=pipeline_name)
                filtered_executions = self._apply_execution_filters(pipeline_executions, filters or {})

                if not filtered_executions and filters:
                    self.console.print(f"[yellow]No executions found for pipeline '{pipeline_name}' with applied filters[/yellow]")
                    return

                # Recalculate stats based on filtered executions if filters are applied
                if filters:
                    stats = self._calculate_filtered_pipeline_stats(pipeline_name, filtered_executions)

                self._print_single_pipeline_stats(pipeline_name, stats, show_tasks, filters)
            else:
                self.console.print(f"[yellow]No statistics found for pipeline: {pipeline_name}[/yellow]")
        else:
            # All pipelines overview with filtering
            all_stats = self.get_pipeline_stats()
            filtered_stats = self._apply_pipeline_filters(self.database.pipelines, filters or {})

            if not filtered_stats:
                self.console.print("[yellow]No pipeline statistics found matching the filters[/yellow]")
                return

            # Convert to dict format for display
            display_stats = {name: stats.model_dump() for name, stats in filtered_stats.items()}
            self._print_all_pipeline_stats(display_stats, show_tasks, filters)

    def _calculate_filtered_pipeline_stats(self, pipeline_name: str, executions: List[PipelineExecution]) -> Dict[str, Any]:
        """Calculate pipeline statistics from filtered executions"""
        if not executions:
            return {}

        total_executions = len(executions)
        successful_executions = sum(1 for e in executions if e.status == TaskStatus.SUCCESS)
        failed_executions = sum(1 for e in executions if e.status == TaskStatus.FAILED)
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

        # Calculate task statistics from filtered executions
        task_statistics = {}
        for execution in executions:
            for task in execution.tasks:
                task_name = task.name
                if task_name not in task_statistics:
                    task_statistics[task_name] = {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'skipped_executions': 0,
                        'success_rate': 0.0
                    }

                task_stats = task_statistics[task_name]
                task_stats['total_executions'] += 1

                if task.status == TaskStatus.SUCCESS:
                    task_stats['successful_executions'] += 1
                elif task.status == TaskStatus.FAILED:
                    task_stats['failed_executions'] += 1
                elif task.status == TaskStatus.SKIPPED:
                    task_stats['skipped_executions'] += 1

                # Update success rate
                if task_stats['total_executions'] > 0:
                    task_stats['success_rate'] = (task_stats['successful_executions'] / task_stats['total_executions']) * 100

        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': success_rate,
            'first_seen': min(e.parsed_at for e in executions) if executions else None,
            'last_seen': max(e.parsed_at for e in executions) if executions else None,
            'repositories': list(set(e.repository for e in executions if e.repository)),
            'task_statistics': task_statistics,
            'filtered': True
        }

    def _print_single_pipeline_stats(self, name: str, stats: Dict[str, Any], show_tasks: bool = False, filters: Optional[Dict[str, Any]] = None) -> None:
        """Print detailed statistics for a single pipeline"""
        # Pipeline overview
        title = f"Pipeline: {name}"
        if filters and stats.get('filtered', False):
            title += " (Filtered)"

        table = Table(title=title)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Executions", str(stats['total_executions']))
        table.add_row("Successful", str(stats['successful_executions']))
        table.add_row("Failed", str(stats['failed_executions']))
        table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")
        table.add_row("First Seen", str(stats['first_seen']))
        table.add_row("Last Seen", str(stats['last_seen']))
        table.add_row("Repositories", ", ".join(stats['repositories']))

        self.console.print(Panel(table, title="🔧 Pipeline Overview", expand=False))

        # Task statistics - always show for single pipeline or when explicitly requested
        if stats['task_statistics'] and (show_tasks or True):
            task_title = "Task Statistics"
            if filters and stats.get('filtered', False):
                task_title += " (Filtered)"

            task_table = Table(title=task_title)
            task_table.add_column("Task Name", style="cyan")
            task_table.add_column("Total", style="white")
            task_table.add_column("Success", style="green")
            task_table.add_column("Failed", style="red")
            task_table.add_column("Skipped", style="yellow")
            task_table.add_column("Success Rate", style="magenta")

            # Sort tasks by success rate (worst first for attention)
            sorted_tasks = sorted(
                stats['task_statistics'].items(),
                key=lambda x: x[1]['success_rate']
            )

            for task_name, task_stats in sorted_tasks:
                task_table.add_row(
                    task_name,
                    str(task_stats['total_executions']),
                    str(task_stats['successful_executions']),
                    str(task_stats['failed_executions']),
                    str(task_stats['skipped_executions']),
                    f"{task_stats['success_rate']:.1f}%"
                )

            self.console.print(Panel(task_table, title="📋 Task Statistics", expand=False))

    def _print_all_pipeline_stats(self, stats: Dict[str, Any], show_tasks: bool = False, filters: Optional[Dict[str, Any]] = None) -> None:
        """Print overview of all pipelines"""
        title = "All Pipelines Overview"
        if filters:
            title += " (Filtered)"

        table = Table(title=title)
        table.add_column("Pipeline Name", style="cyan")
        table.add_column("Total Executions", style="white")
        table.add_column("Success Rate", style="magenta")
        table.add_column("Total Tasks", style="blue")
        table.add_column("Last Seen", style="yellow")
        table.add_column("Repositories", style="green")

        for name, pipeline_stats in stats.items():
            total_tasks = len(pipeline_stats['task_statistics'])
            table.add_row(
                name,
                str(pipeline_stats['total_executions']),
                f"{pipeline_stats['success_rate']:.1f}%",
                str(total_tasks),
                str(pipeline_stats['last_seen']),
                str(len(pipeline_stats['repositories']))
            )

        self.console.print(Panel(table, title="📊 All Pipelines", expand=False))

        # Show task statistics if requested
        if show_tasks:
            self._print_task_summary(stats, filters)

    def _print_task_summary(self, stats: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> None:
        """Print task statistics summary across all pipelines"""
        # Collect all task statistics
        all_task_stats = {}

        for pipeline_name, pipeline_stats in stats.items():
            for task_name, task_stats in pipeline_stats['task_statistics'].items():
                if task_name not in all_task_stats:
                    all_task_stats[task_name] = {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'skipped_executions': 0,
                        'pipelines': []
                    }

                all_task_stats[task_name]['total_executions'] += task_stats['total_executions']
                all_task_stats[task_name]['successful_executions'] += task_stats['successful_executions']
                all_task_stats[task_name]['failed_executions'] += task_stats['failed_executions']
                all_task_stats[task_name]['skipped_executions'] += task_stats['skipped_executions']
                all_task_stats[task_name]['pipelines'].append(pipeline_name)

        # Calculate success rates
        for task_name, task_stats in all_task_stats.items():
            if task_stats['total_executions'] > 0:
                task_stats['success_rate'] = (task_stats['successful_executions'] / task_stats['total_executions']) * 100
            else:
                task_stats['success_rate'] = 0.0

        # Create task summary table
        title = "Task Statistics Summary (All Pipelines)"
        if filters:
            title += " (Filtered)"

        task_table = Table(title=title)
        task_table.add_column("Task Name", style="cyan")
        task_table.add_column("Total", style="white")
        task_table.add_column("Success", style="green")
        task_table.add_column("Failed", style="red")
        task_table.add_column("Skipped", style="yellow")
        task_table.add_column("Success Rate", style="magenta")
        task_table.add_column("Pipelines", style="blue")

        # Sort by success rate (worst first)
        sorted_tasks = sorted(
            all_task_stats.items(),
            key=lambda x: x[1]['success_rate']
        )

        for task_name, task_stats in sorted_tasks:
            task_table.add_row(
                task_name,
                str(task_stats['total_executions']),
                str(task_stats['successful_executions']),
                str(task_stats['failed_executions']),
                str(task_stats['skipped_executions']),
                f"{task_stats['success_rate']:.1f}%",
                str(len(set(task_stats['pipelines'])))
            )

        self.console.print(Panel(task_table, title="📋 Task Statistics Summary", expand=False))

    def get_task_stats(self, task_name: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get task statistics across all pipelines with optional filtering"""
        all_task_stats = {}

        # Apply pipeline-level filters first
        filtered_pipelines = self._apply_pipeline_filters(self.database.pipelines, filters or {})

        for pipeline_name, pipeline_stats in filtered_pipelines.items():
            # Apply pipeline name filter if specified
            if filters and 'pipeline' in filters and pipeline_name != filters['pipeline']:
                continue

            for t_name, task_stats in pipeline_stats.task_statistics.items():
                # Filter by task name if provided
                if task_name and t_name != task_name:
                    continue

                if t_name not in all_task_stats:
                    all_task_stats[t_name] = {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'skipped_executions': 0,
                        'pipelines': [],
                        'pipeline_stats': {}
                    }

                all_task_stats[t_name]['total_executions'] += task_stats['total_executions']
                all_task_stats[t_name]['successful_executions'] += task_stats['successful_executions']
                all_task_stats[t_name]['failed_executions'] += task_stats['failed_executions']
                all_task_stats[t_name]['skipped_executions'] += task_stats['skipped_executions']
                all_task_stats[t_name]['pipelines'].append(pipeline_name)
                all_task_stats[t_name]['pipeline_stats'][pipeline_name] = task_stats

        # Calculate success rates
        for t_name, task_stats in all_task_stats.items():
            if task_stats['total_executions'] > 0:
                task_stats['success_rate'] = (task_stats['successful_executions'] / task_stats['total_executions']) * 100
            else:
                task_stats['success_rate'] = 0.0

        return all_task_stats

    def print_task_stats(self, task_name: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> None:
        """Print task statistics with optional filtering"""
        task_stats = self.get_task_stats(task_name, filters)

        if not task_stats:
            self.console.print("[yellow]No task statistics found matching the filters[/yellow]")
            return

        # Show filter info
        if filters or task_name:
            filter_info = []
            if task_name:
                filter_info.append(f"Task: {task_name}")
            if filters:
                if 'repository' in filters:
                    filter_info.append(f"Repository: {filters['repository']}")
                if 'pipeline' in filters:
                    filter_info.append(f"Pipeline: {filters['pipeline']}")
                if 'min_executions' in filters and filters['min_executions'] > 1:
                    filter_info.append(f"Min executions: {filters['min_executions']}")

            if filter_info:
                self.console.print(f"[blue]🔍 Applied filters: {', '.join(filter_info)}[/blue]")

        if task_name:
            # Single task details
            self._print_single_task_stats(task_name, task_stats.get(task_name, {}), filters)
        else:
            # All tasks overview
            self._print_all_task_stats(task_stats, filters)

    def _print_single_task_stats(self, task_name: str, stats: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> None:
        """Print detailed statistics for a single task"""
        if not stats:
            self.console.print(f"[yellow]No statistics found for task: {task_name}[/yellow]")
            return

        # Task overview
        title = f"Task: {task_name}"
        if filters:
            title += " (Filtered)"

        table = Table(title=title)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Executions", str(stats['total_executions']))
        table.add_row("Successful", str(stats['successful_executions']))
        table.add_row("Failed", str(stats['failed_executions']))
        table.add_row("Skipped", str(stats['skipped_executions']))
        table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")
        table.add_row("Used in Pipelines", str(len(set(stats['pipelines']))))

        self.console.print(Panel(table, title="📋 Task Overview", expand=False))

        # Pipeline breakdown
        if stats['pipeline_stats']:
            breakdown_title = "Pipeline Breakdown"
            if filters:
                breakdown_title += " (Filtered)"

            pipeline_table = Table(title=breakdown_title)
            pipeline_table.add_column("Pipeline", style="cyan")
            pipeline_table.add_column("Total", style="white")
            pipeline_table.add_column("Success", style="green")
            pipeline_table.add_column("Failed", style="red")
            pipeline_table.add_column("Success Rate", style="magenta")

            for pipeline_name, pipeline_stats in stats['pipeline_stats'].items():
                pipeline_table.add_row(
                    pipeline_name,
                    str(pipeline_stats['total_executions']),
                    str(pipeline_stats['successful_executions']),
                    str(pipeline_stats['failed_executions']),
                    f"{pipeline_stats['success_rate']:.1f}%"
                )

            self.console.print(Panel(pipeline_table, title="🔧 Pipeline Breakdown", expand=False))

    def _print_all_task_stats(self, stats: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> None:
        """Print overview of all tasks"""
        title = "All Tasks Overview"
        if filters:
            title += " (Filtered)"

        table = Table(title=title)
        table.add_column("Task Name", style="cyan")
        table.add_column("Total Executions", style="white")
        table.add_column("Success Rate", style="magenta")
        table.add_column("Failed", style="red")
        table.add_column("Pipelines", style="blue")

        # Sort by success rate (worst first)
        sorted_tasks = sorted(
            stats.items(),
            key=lambda x: x[1]['success_rate']
        )

        for task_name, task_stats in sorted_tasks:
            table.add_row(
                task_name,
                str(task_stats['total_executions']),
                f"{task_stats['success_rate']:.1f}%",
                str(task_stats['failed_executions']),
                str(len(set(task_stats['pipelines'])))
            )

        self.console.print(Panel(table, title="📋 All Tasks", expand=False))

    def export_to_json(self, filename: Optional[str] = None) -> str:
        """Export statistics to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pipeline_stats_export_{timestamp}.json"

        filepath = self.data_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(self.database.model_dump(), f, indent=2, default=str)

            self.console.print(f"[green]Statistics exported to: {filepath}[/green]")
            return str(filepath)
        except Exception as e:
            self.console.print(f"[red]Error exporting statistics: {e}[/red]")
            return ""

    def get_pipeline_logs(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get pipeline executions with log URLs based on filters"""
        executions = self.database.executions
        log_entries = []

        # Apply basic execution filters
        if 'repository' in filters:
            executions = [e for e in executions if e.repository == filters['repository']]

        if 'pipeline' in filters:
            executions = [e for e in executions if e.name == filters['pipeline']]

        if 'status' in filters:
            executions = [e for e in executions if e.status == filters['status']]

        # Process each execution
        for execution in executions:
            # If filtering by task, check individual tasks
            if 'task' in filters or 'task_status' in filters:
                for task in execution.tasks:
                    # Apply task filters
                    if 'task' in filters and task.name != filters['task']:
                        continue

                    if 'task_status' in filters and task.status != filters['task_status']:
                        continue

                    # Create log entry for this task
                    log_entry = {
                        'pipeline_name': execution.name,
                        'pipelinerun_name': execution.pipelinerun_name,
                        'task_name': task.name,
                        'task_status': task.status,
                        'task_duration': task.duration,
                        'pipeline_status': execution.status,
                        'pipeline_logs_url': execution.pipeline_logs_url,
                        'troubleshooting_guide_url': execution.troubleshooting_guide_url,
                        'restart_command': execution.restart_command,
                        'pr_number': execution.pr_number,
                        'pr_url': execution.pr_url,
                        'repository': execution.repository,
                        'parsed_at': execution.parsed_at,
                        'start_time': execution.start_time,
                        'execution_type': 'task'
                    }
                    log_entries.append(log_entry)
            else:
                # No task-specific filtering, add pipeline-level entry
                log_entry = {
                    'pipeline_name': execution.name,
                    'pipelinerun_name': execution.pipelinerun_name,
                    'task_name': None,
                    'task_status': None,
                    'task_duration': None,
                    'pipeline_status': execution.status,
                    'pipeline_logs_url': execution.pipeline_logs_url,
                    'troubleshooting_guide_url': execution.troubleshooting_guide_url,
                    'restart_command': execution.restart_command,
                    'pr_number': execution.pr_number,
                    'pr_url': execution.pr_url,
                    'repository': execution.repository,
                    'parsed_at': execution.parsed_at,
                    'start_time': execution.start_time,
                    'execution_type': 'pipeline'
                }
                log_entries.append(log_entry)

        # Sort by parsed_at (newest first)
        log_entries.sort(key=lambda x: x['parsed_at'], reverse=True)

        # Apply limit
        if 'limit' in filters:
            log_entries = log_entries[:filters['limit']]

        return log_entries

    def print_pipeline_logs(self, filters: Dict[str, Any]) -> None:
        """Print pipeline log URLs with filtering"""
        log_entries = self.get_pipeline_logs(filters)

        if not log_entries:
            self.console.print("[yellow]No pipeline logs found matching the filters[/yellow]")
            return

        # Determine if we're showing task-level or pipeline-level logs
        showing_tasks = any('task' in filters or 'task_status' in filters for filters in [filters])

        # Create table
        if showing_tasks:
            title = f"Pipeline Logs - Task Level ({len(log_entries)} entries)"
            table = Table(title=title)
            table.add_column("Pipeline", style="cyan", max_width=25)
            table.add_column("Task", style="yellow", max_width=20)
            table.add_column("Task Status", style="magenta", max_width=12)
            table.add_column("Duration", style="white", max_width=10)
            table.add_column("Pipeline Logs", style="blue")
            table.add_column("PR", style="green", max_width=8)
            table.add_column("Repository", style="dim", max_width=20)
            table.add_column("Date", style="dim", max_width=12)
        else:
            title = f"Pipeline Logs - Pipeline Level ({len(log_entries)} entries)"
            table = Table(title=title)
            table.add_column("Pipeline", style="cyan", max_width=25)
            table.add_column("PipelineRun", style="dim", max_width=20)
            table.add_column("Status", style="magenta", max_width=12)
            table.add_column("Pipeline Logs", style="blue")
            table.add_column("PR", style="green", max_width=8)
            table.add_column("Repository", style="yellow", max_width=20)
            table.add_column("Date", style="dim", max_width=12)

        # Add rows
        for entry in log_entries:
            # Format status with emoji
            if showing_tasks:
                status_emoji = {
                    TaskStatus.SUCCESS: "✅",
                    TaskStatus.FAILED: "❌",
                    TaskStatus.SKIPPED: "⏭️",
                    TaskStatus.RUNNING: "🔄",
                    TaskStatus.PENDING: "⏸️",
                    TaskStatus.UNKNOWN: "❓"
                }.get(entry['task_status'], "❓")

                status_display = f"{status_emoji} {entry['task_status'].value if entry['task_status'] else 'N/A'}"
            else:
                status_emoji = {
                    TaskStatus.SUCCESS: "✅",
                    TaskStatus.FAILED: "❌",
                    TaskStatus.SKIPPED: "⏭️",
                    TaskStatus.RUNNING: "🔄",
                    TaskStatus.PENDING: "⏸️",
                    TaskStatus.UNKNOWN: "❓"
                }.get(entry['pipeline_status'], "❓")

                status_display = f"{status_emoji} {entry['pipeline_status'].value if entry['pipeline_status'] else 'N/A'}"

            # Format other fields
            pr_display = f"#{entry['pr_number']}" if entry['pr_number'] else "N/A"
            date_display = entry['parsed_at'].strftime('%Y-%m-%d') if entry['parsed_at'] else "N/A"
            logs_display = entry['pipeline_logs_url'] if entry['pipeline_logs_url'] else "No logs"
            duration_display = entry['task_duration'] if entry['task_duration'] else "N/A"

            if showing_tasks:
                table.add_row(
                    entry['pipeline_name'] or "N/A",
                    entry['task_name'] or "N/A",
                    status_display,
                    duration_display,
                    logs_display,
                    pr_display,
                    entry['repository'] or "N/A",
                    date_display
                )
            else:
                table.add_row(
                    entry['pipeline_name'] or "N/A",
                    entry['pipelinerun_name'] or "N/A",
                    status_display,
                    logs_display,
                    pr_display,
                    entry['repository'] or "N/A",
                    date_display
                )

        self.console.print(Panel(table, title="🔗 Pipeline Logs", expand=False))

        # Show URLs in a cleaner format
        if log_entries:
            self.console.print("\n[bold blue]📋 Full URLs for Copy/Paste:[/bold blue]")

            # Group by unique URLs to avoid duplicates
            unique_urls = {}
            for entry in log_entries:
                if entry['pipeline_logs_url'] and entry['pipeline_logs_url'] != "No logs":
                    key = f"{entry['pipeline_name']}"
                    if entry['task_name']:
                        key += f" - {entry['task_name']}"

                    if entry['pipeline_logs_url'] not in unique_urls.values():
                        unique_urls[key] = entry['pipeline_logs_url']

            # Display unique URLs
            for key, url in list(unique_urls.items())[:10]:  # Limit to first 10 to avoid spam
                self.console.print(f"  [cyan]{key}:[/cyan]")
                self.console.print(f"    {url}")

            if len(unique_urls) > 10:
                self.console.print(f"  [dim]... and {len(unique_urls) - 10} more URLs[/dim]")

        # Show additional information if available
        sample_entry = log_entries[0] if log_entries else {}
        additional_info = []

        if sample_entry.get('troubleshooting_guide_url'):
            additional_info.append(("Troubleshooting Guide", sample_entry['troubleshooting_guide_url']))

        if sample_entry.get('restart_command'):
            additional_info.append(("Restart Command", sample_entry['restart_command']))

        if additional_info:
            self.console.print("\n[bold blue]🛠️  Additional Resources:[/bold blue]")
            for label, info in additional_info:
                self.console.print(f"  [cyan]{label}:[/cyan]")
                self.console.print(f"    {info}")
