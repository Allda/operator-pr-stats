"""
Main CLI application for parsing Tekton pipeline summaries from GitHub PR comments
"""
import os
from typing import Optional, List
from datetime import datetime
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt

from github_client import GitHubClient
from parser import TektonPipelineParser
from stats_manager import StatisticsManager
from models import TaskStatus

app = typer.Typer(help="Parse Tekton pipeline summaries from GitHub PR comments")
console = Console()


@app.command()
def parse(
    repository: str = typer.Argument(..., help="GitHub repository in format 'owner/repo'"),
    pr_number: Optional[int] = typer.Option(None, "--pr", help="Specific PR number to parse"),
    limit: int = typer.Option(50, "--limit", help="Maximum number of PRs to check"),
    days_back: int = typer.Option(30, "--days", help="Number of days back to search"),
    max_prs: int = typer.Option(500, "--max-prs", help="Maximum number of PRs to fetch initially"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory to store statistics"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token (or set GITHUB_TOKEN env var)"),
):
    """Parse pipeline summaries from GitHub PR comments"""

    try:
        # Initialize components
        github_client = GitHubClient(token)
        parser = TektonPipelineParser()
        stats_manager = StatisticsManager(data_dir)

        console.print(f"[bold blue]Parsing pipeline summaries from {repository}[/bold blue]")

        # Get repository info
        repo_info = github_client.get_repository_info(repository)
        if repo_info:
            console.print(f"Repository: {repo_info['full_name']}")
            console.print(f"Description: {repo_info.get('description', 'N/A')}")

        # Search for pipeline comments
        if pr_number:
            # Get comments from specific PR
            console.print(f"[blue]📄 Fetching comments from PR #{pr_number}[/blue]")
            comments = github_client.get_pr_comments(repository, pr_number)
            console.print(f"[green]✅ Found {len(comments)} comments in PR #{pr_number}[/green]")
        else:
            # Search for pipeline comments in recent PRs
            comments = github_client.search_pipeline_comments(
                repository, limit=limit, days_back=days_back, max_prs=max_prs
            )

        if not comments:
            console.print("[yellow]❌ No pipeline comments found[/yellow]")
            return

        # Parse comments
        console.print(f"[blue]⚙️ Parsing {len(comments)} comments for pipeline summaries[/blue]")

        executions = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False
        ) as progress:
            parse_task = progress.add_task("Parsing pipeline summaries...", total=len(comments))

            for i, comment in enumerate(comments):
                progress.update(parse_task, description=f"Parsing comment {i+1}/{len(comments)}")

                execution = parser.parse_pipeline_summary(
                    comment['body'],
                    pr_number=comment.get('pr_number'),
                    pr_url=comment.get('pr_url'),
                    comment_id=comment.get('id'),
                    repository=repository
                )

                if execution:
                    executions.append(execution)

                progress.advance(parse_task)

        if not executions:
            console.print("[yellow]❌ No valid pipeline summaries found[/yellow]")
            return

        # Add to statistics
        console.print(f"[blue]💾 Saving {len(executions)} pipeline executions to database[/blue]")
        stats_manager.add_executions(executions)

        console.print(f"[green]✅ Successfully saved {len(executions)} pipeline executions[/green]")

        # Show summary
        console.print("\n[bold blue]📊 Updated Statistics Summary[/bold blue]")
        stats_manager.print_summary()

        console.print(f"\n[bold green]🎉 Processing complete! {len(executions)} new pipeline executions added to database.[/bold green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats(
    pipeline: Optional[str] = typer.Option(None, "--pipeline", help="Show stats for specific pipeline"),
    repository: Optional[str] = typer.Option(None, "--repository", help="Filter by repository (e.g., 'owner/repo')"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (success/failed/etc.)"),
    show_tasks: bool = typer.Option(False, "--show-tasks", help="Show task statistics"),
    min_executions: int = typer.Option(1, "--min-executions", help="Minimum number of executions to show"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory with statistics data"),
):
    """Show pipeline statistics with filtering options"""

    try:
        stats_manager = StatisticsManager(data_dir)

        # Convert status string to TaskStatus enum if provided
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status.lower())
            except ValueError:
                console.print(f"[red]Invalid status: {status}. Valid options: success, failed, skipped, running, pending, unknown[/red]")
                raise typer.Exit(1)

        # Create filter criteria
        filters = {
            'repository': repository,
            'status': status_filter,
            'min_executions': min_executions
        }

        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}

        # Show filter info if any filters are applied
        if filters or pipeline:
            filter_info = []
            if pipeline:
                filter_info.append(f"Pipeline: {pipeline}")
            if repository:
                filter_info.append(f"Repository: {repository}")
            if status:
                filter_info.append(f"Status: {status}")
            if min_executions > 1:
                filter_info.append(f"Min executions: {min_executions}")

            console.print(f"[blue]🔍 Applying filters: {', '.join(filter_info)}[/blue]")

        if pipeline:
            stats_manager.print_pipeline_stats(pipeline, show_tasks, filters)
        else:
            stats_manager.print_summary(filters)
            console.print()
            stats_manager.print_pipeline_stats(show_tasks=show_tasks, filters=filters)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def tasks(
    task: Optional[str] = typer.Option(None, "--task", help="Show stats for specific task"),
    repository: Optional[str] = typer.Option(None, "--repository", help="Filter by repository (e.g., 'owner/repo')"),
    pipeline: Optional[str] = typer.Option(None, "--pipeline", help="Filter by pipeline name"),
    min_executions: int = typer.Option(1, "--min-executions", help="Minimum number of executions to show"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory with statistics data"),
):
    """Show task statistics across all pipelines with filtering options"""

    try:
        stats_manager = StatisticsManager(data_dir)

        # Create filter criteria
        filters = {
            'repository': repository,
            'pipeline': pipeline,
            'min_executions': min_executions
        }

        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}

        # Show filter info if any filters are applied
        if filters or task:
            filter_info = []
            if task:
                filter_info.append(f"Task: {task}")
            if repository:
                filter_info.append(f"Repository: {repository}")
            if pipeline:
                filter_info.append(f"Pipeline: {pipeline}")
            if min_executions > 1:
                filter_info.append(f"Min executions: {min_executions}")

            console.print(f"[blue]🔍 Applying filters: {', '.join(filter_info)}[/blue]")

        if task:
            stats_manager.print_task_stats(task, filters)
        else:
            stats_manager.print_task_stats(filters=filters)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_executions(
    pipeline: Optional[str] = typer.Option(None, "--pipeline", help="Filter by pipeline name"),
    repository: Optional[str] = typer.Option(None, "--repository", help="Filter by repository"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (success/failed/etc.)"),
    limit: int = typer.Option(10, "--limit", help="Maximum number of executions to show"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory with statistics data"),
):
    """List recent pipeline executions"""

    try:
        stats_manager = StatisticsManager(data_dir)

        # Convert status string to TaskStatus enum
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status.lower())
            except ValueError:
                console.print(f"[red]Invalid status: {status}. Valid options: success, failed, skipped, running, pending, unknown[/red]")
                raise typer.Exit(1)

        executions = stats_manager.get_executions(
            pipeline_name=pipeline,
            repository=repository,
            status=status_filter,
            limit=limit
        )

        if not executions:
            console.print("[yellow]No executions found matching the criteria[/yellow]")
            return

        # Create executions table
        from rich.table import Table

        table = Table(title=f"Recent Pipeline Executions ({len(executions)} shown)")
        table.add_column("Pipeline", style="cyan")
        table.add_column("PipelineRun", style="dim")
        table.add_column("Status", style="magenta")
        table.add_column("Success Rate", style="green")
        table.add_column("Tasks", style="white")
        table.add_column("Repository", style="yellow")
        table.add_column("PR", style="blue")
        table.add_column("Date", style="dim")

        for execution in executions:
            # Format status with emoji
            status_emoji = {
                TaskStatus.SUCCESS: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.SKIPPED: "⏭️",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.PENDING: "⏸️",
                TaskStatus.UNKNOWN: "❓"
            }.get(execution.status, "❓")

            status_display = f"{status_emoji} {execution.status.value}"

            success_rate = f"{execution.success_rate:.1f}%" if execution.success_rate else "N/A"
            tasks_display = f"{execution.successful_tasks}/{execution.total_tasks}"
            pr_display = f"#{execution.pr_number}" if execution.pr_number else "N/A"
            date_display = execution.parsed_at.strftime("%Y-%m-%d %H:%M")

            table.add_row(
                execution.name,
                execution.pipelinerun_name or "N/A",
                status_display,
                success_rate,
                tasks_display,
                execution.repository or "N/A",
                pr_display,
                date_display
            )

        console.print(Panel(table, title="📋 Pipeline Executions", expand=False))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    filename: Optional[str] = typer.Option(None, "--filename", help="Export filename"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory with statistics data"),
):
    """Export statistics to JSON file"""

    try:
        stats_manager = StatisticsManager(data_dir)
        filepath = stats_manager.export_to_json(filename)

        if filepath:
            console.print(f"[green]✅ Statistics exported to: {filepath}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test_parser(
    comment_file: str = typer.Argument(..., help="Path to file containing a sample comment"),
):
    """Test the parser with a sample comment"""

    try:
        with open(comment_file, 'r') as f:
            comment_body = f.read()

        parser = TektonPipelineParser()

        if not parser.is_pipeline_summary(comment_body):
            console.print("[yellow]This comment does not appear to contain a pipeline summary[/yellow]")
            return

        execution = parser.parse_pipeline_summary(
            comment_body,
            pr_number=123,
            pr_url="https://github.com/test/repo/pull/123",
            comment_id=456,
            repository="test/repo"
        )

        if execution:
            console.print("[green]✅ Successfully parsed pipeline summary[/green]")
            console.print(f"Pipeline: {execution.name}")
            if execution.pipelinerun_name:
                console.print(f"PipelineRun: {execution.pipelinerun_name}")
            console.print(f"Status: {execution.status.value}")
            console.print(f"Success Rate: {execution.success_rate}%")
            console.print(f"Tasks: {execution.total_tasks} total, {execution.successful_tasks} successful")

            if execution.start_time:
                console.print(f"Start Time: {execution.start_time}")
            if execution.pipeline_logs_url:
                console.print(f"Pipeline Logs:")
                console.print(f"  {execution.pipeline_logs_url}")
            if execution.troubleshooting_guide_url:
                console.print(f"Troubleshooting Guide:")
                console.print(f"  {execution.troubleshooting_guide_url}")
            if execution.restart_command:
                console.print(f"Restart Command: {execution.restart_command}")

            if execution.tasks:
                console.print("\nTasks:")
                for task in execution.tasks:
                    status_emoji = {
                        TaskStatus.SUCCESS: "✅",
                        TaskStatus.FAILED: "❌",
                        TaskStatus.SKIPPED: "⏭️",
                        TaskStatus.RUNNING: "🔄",
                        TaskStatus.PENDING: "⏸️",
                        TaskStatus.UNKNOWN: "❓"
                    }.get(task.status, "❓")

                    task_info = f"  {status_emoji} {task.name}"
                    if task.duration:
                        task_info += f" ({task.duration})"
                    if task.start_time:
                        task_info += f" - {task.start_time.strftime('%H:%M:%S')}"

                    console.print(task_info)
        else:
            console.print("[red]❌ Failed to parse pipeline summary[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def setup():
    """Interactive setup for GitHub token and configuration"""

    console.print(Panel("🔧 Setup GitHub Pipeline Parser", style="bold blue"))

    # Check for existing token
    existing_token = os.getenv('GITHUB_TOKEN')
    if existing_token:
        console.print(f"[green]✅ Found existing GITHUB_TOKEN environment variable[/green]")
    else:
        console.print("[yellow]ℹ️  No GITHUB_TOKEN found in environment[/yellow]")
        console.print("\nTo use this tool, you need a GitHub Personal Access Token.")
        console.print("Create one at: https://github.com/settings/tokens")
        console.print("Required permissions: repo (if accessing private repos) or public_repo")

        token = Prompt.ask("Enter your GitHub token", password=True)

        # Test the token
        try:
            client = GitHubClient(token)
            rate_limit = client.get_rate_limit()
            console.print(f"[green]✅ Token is valid! Rate limit: {rate_limit['core']['remaining']}/{rate_limit['core']['limit']}[/green]")

            # Ask if user wants to save token
            save_token = typer.confirm("Would you like to save this token to a .env file?")
            if save_token:
                with open('.env', 'w') as f:
                    f.write(f"GITHUB_TOKEN={token}\n")
                console.print("[green]✅ Token saved to .env file[/green]")
                console.print("[yellow]ℹ️  Remember to add .env to your .gitignore file[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Token validation failed: {e}[/red]")
            raise typer.Exit(1)

    # Create data directory
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    console.print(f"[green]✅ Data directory created: {data_dir}[/green]")

    console.print("\n[bold green]🎉 Setup complete![/bold green]")
    console.print("You can now use the tool to parse pipeline summaries:")
    console.print("  [cyan]python main.py parse owner/repo[/cyan]")


@app.command()
def logs(
    task: Optional[str] = typer.Option(None, "--task", help="Filter by specific task name"),
    pipeline: Optional[str] = typer.Option(None, "--pipeline", help="Filter by pipeline name"),
    repository: Optional[str] = typer.Option(None, "--repository", help="Filter by repository (e.g., 'owner/repo')"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (success/failed/etc.)"),
    task_status: Optional[str] = typer.Option(None, "--task-status", help="Filter by task status (success/failed/etc.)"),
    limit: int = typer.Option(20, "--limit", help="Maximum number of logs to show"),
    data_dir: str = typer.Option("data", "--data-dir", help="Directory with statistics data"),
):
    """Show pipeline log URLs with filtering options for debugging"""

    try:
        stats_manager = StatisticsManager(data_dir)

        # Convert status strings to TaskStatus enums if provided
        status_filter = None
        task_status_filter = None

        if status:
            try:
                status_filter = TaskStatus(status.lower())
            except ValueError:
                console.print(f"[red]Invalid status: {status}. Valid options: success, failed, skipped, running, pending, unknown[/red]")
                raise typer.Exit(1)

        if task_status:
            try:
                task_status_filter = TaskStatus(task_status.lower())
            except ValueError:
                console.print(f"[red]Invalid task-status: {task_status}. Valid options: success, failed, skipped, running, pending, unknown[/red]")
                raise typer.Exit(1)

        # Create filter criteria
        filters = {
            'task': task,
            'pipeline': pipeline,
            'repository': repository,
            'status': status_filter,
            'task_status': task_status_filter,
            'limit': limit
        }

        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}

        # Show filter info
        filter_info = []
        if task:
            filter_info.append(f"Task: {task}")
        if pipeline:
            filter_info.append(f"Pipeline: {pipeline}")
        if repository:
            filter_info.append(f"Repository: {repository}")
        if status:
            filter_info.append(f"Pipeline status: {status}")
        if task_status:
            filter_info.append(f"Task status: {task_status}")
        if limit != 20:
            filter_info.append(f"Limit: {limit}")

        if filter_info:
            console.print(f"[blue]🔍 Applying filters: {', '.join(filter_info)}[/blue]")

        # Get and display logs
        stats_manager.print_pipeline_logs(filters)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
