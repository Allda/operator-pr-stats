"""
Parser for Tekton pipeline summaries from GitHub PR comments
"""
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from models import PipelineExecution, TaskExecution, TaskStatus


class TektonPipelineParser:
    """Parser for Tekton pipeline summaries in GitHub PR comments"""

    def __init__(self):
        # Common patterns for parsing pipeline summaries
        self.pipeline_summary_start = re.compile(r'#\s*Pipeline Summary', re.IGNORECASE)
        self.pipeline_name_pattern = re.compile(r'Pipeline:\s*[*_]?([^*_\n]+)[*_]?', re.IGNORECASE)
        self.pipelinerun_name_pattern = re.compile(r'PipelineRun:\s*[*_]?([^*_\n]+)[*_]?', re.IGNORECASE)
        self.start_time_pattern = re.compile(r'Start Time:\s*[*_]?([^*_\n]+)[*_]?', re.IGNORECASE)
        self.success_rate_pattern = re.compile(r'Success Rate:\s*(\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
        self.duration_pattern = re.compile(r'Duration:\s*([^:\n]+)', re.IGNORECASE)
        self.pipeline_logs_pattern = re.compile(r'Pipeline logs:\s*(https?://[^\s\n]+)', re.IGNORECASE)
        self.troubleshooting_guide_pattern = re.compile(r'\[troubleshooting guide\]\(([^)]+)\)', re.IGNORECASE)
        self.restart_command_pattern = re.compile(r'Run\s+`([^`]+)`\s+in case of pipeline failure', re.IGNORECASE)

        # Task patterns - support both list and table formats
        self.task_pattern = re.compile(r'[-*]\s*(.+?):\s*(✅|❌|⏭️|🔄|⏸️|❓)', re.IGNORECASE)
        self.task_detail_pattern = re.compile(r'[-*]\s*(.+?):\s*(✅|❌|⏭️|🔄|⏸️|❓)(?:\s*\(([^)]+)\))?', re.IGNORECASE)

        # Table format task pattern
        self.task_table_pattern = re.compile(r'\|\s*(:\w+:|[\w\s]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', re.IGNORECASE)

        # Status mapping - including GitHub emoji codes
        self.status_mapping = {
            '✅': TaskStatus.SUCCESS,
            '❌': TaskStatus.FAILED,
            '⏭️': TaskStatus.SKIPPED,
            '🔄': TaskStatus.RUNNING,
            '⏸️': TaskStatus.PENDING,
            '❓': TaskStatus.UNKNOWN,
            ':heavy_check_mark:': TaskStatus.SUCCESS,
            ':x:': TaskStatus.FAILED,
            ':fast_forward:': TaskStatus.SKIPPED,
            ':arrows_counterclockwise:': TaskStatus.RUNNING,
            ':pause_button:': TaskStatus.PENDING,
            ':question:': TaskStatus.UNKNOWN,
        }

    def is_pipeline_summary(self, comment_body: str) -> bool:
        """Check if comment contains a pipeline summary"""
        return bool(self.pipeline_summary_start.search(comment_body))

    def parse_pipeline_summary(self, comment_body: str, pr_number: int = None,
                             pr_url: str = None, comment_id: int = None,
                             repository: str = None) -> Optional[PipelineExecution]:
        """Parse a pipeline summary from comment body"""
        if not self.is_pipeline_summary(comment_body):
            return None

        # Extract pipeline name
        pipeline_name = self._extract_pipeline_name(comment_body)
        if not pipeline_name:
            # Try to extract from context or use default
            pipeline_name = "unknown-pipeline"

        # Extract additional pipeline information
        pipelinerun_name = self._extract_pipelinerun_name(comment_body)
        start_time = self._extract_start_time(comment_body)
        pipeline_logs_url = self._extract_pipeline_logs_url(comment_body)
        troubleshooting_guide_url = self._extract_troubleshooting_guide_url(comment_body)
        restart_command = self._extract_restart_command(comment_body)

        # Extract success rate
        success_rate = self._extract_success_rate(comment_body)

        # Extract duration
        duration = self._extract_duration(comment_body)

        # Extract tasks (try table format first, then list format)
        tasks = self._extract_tasks_from_table(comment_body)
        if not tasks:
            tasks = self._extract_tasks(comment_body)

        # Calculate task statistics
        total_tasks = len(tasks)
        successful_tasks = sum(1 for task in tasks if task.status == TaskStatus.SUCCESS)
        failed_tasks = sum(1 for task in tasks if task.status == TaskStatus.FAILED)
        skipped_tasks = sum(1 for task in tasks if task.status == TaskStatus.SKIPPED)

        # Calculate success rate if not explicitly provided
        if success_rate is None and total_tasks > 0:
            success_rate = (successful_tasks / total_tasks) * 100

        # Determine overall pipeline status
        if failed_tasks > 0:
            pipeline_status = TaskStatus.FAILED
        elif successful_tasks == total_tasks and total_tasks > 0:
            pipeline_status = TaskStatus.SUCCESS
        elif any(task.status == TaskStatus.RUNNING for task in tasks):
            pipeline_status = TaskStatus.RUNNING
        else:
            pipeline_status = TaskStatus.UNKNOWN

        # Create pipeline execution
        execution = PipelineExecution(
            name=pipeline_name,
            pipelinerun_name=pipelinerun_name,
            status=pipeline_status,
            success_rate=success_rate,
            total_tasks=total_tasks,
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            skipped_tasks=skipped_tasks,
            tasks=tasks,
            duration=duration,
            start_time=start_time,
            pipeline_logs_url=pipeline_logs_url,
            troubleshooting_guide_url=troubleshooting_guide_url,
            restart_command=restart_command,
            pr_number=pr_number,
            pr_url=pr_url,
            comment_id=comment_id,
            repository=repository
        )

        return execution

    def _extract_pipeline_name(self, comment_body: str) -> Optional[str]:
        """Extract pipeline name from comment"""
        match = self.pipeline_name_pattern.search(comment_body)
        if match:
            return match.group(1).strip()

        # Try alternative patterns
        alt_patterns = [
            re.compile(r'#\s*Pipeline:\s*(.+)', re.IGNORECASE),
            re.compile(r'Pipeline\s*Name:\s*(.+)', re.IGNORECASE),
            re.compile(r'Running pipeline:\s*(.+)', re.IGNORECASE),
        ]

        for pattern in alt_patterns:
            match = pattern.search(comment_body)
            if match:
                return match.group(1).strip('`" \n\t')

        return None

    def _extract_success_rate(self, comment_body: str) -> Optional[float]:
        """Extract success rate percentage from comment"""
        match = self.success_rate_pattern.search(comment_body)
        if match:
            return float(match.group(1))
        return None

    def _extract_duration(self, comment_body: str) -> Optional[str]:
        """Extract pipeline duration from comment"""
        match = self.duration_pattern.search(comment_body)
        if match:
            return match.group(1).strip()
        return None

    def _extract_tasks(self, comment_body: str) -> List[TaskExecution]:
        """Extract task information from comment"""
        tasks = []

        # Find all task matches
        matches = self.task_detail_pattern.findall(comment_body)

        for match in matches:
            task_name = match[0].strip()
            status_symbol = match[1]
            additional_info = match[2] if len(match) > 2 else ""

            # Map status symbol to TaskStatus
            status = self.status_mapping.get(status_symbol, TaskStatus.UNKNOWN)

            # Extract duration or error message from additional info
            duration = None
            error_message = None

            if additional_info:
                # Check if it looks like a duration (e.g., "2m30s", "1h5m")
                if re.match(r'^\d+[hms]', additional_info):
                    duration = additional_info
                elif status == TaskStatus.FAILED:
                    error_message = additional_info

            task = TaskExecution(
                name=task_name,
                status=status,
                duration=duration,
                error_message=error_message
            )
            tasks.append(task)

        return tasks

    def parse_multiple_comments(self, comments: List[Dict[str, Any]],
                              repository: str = None) -> List[PipelineExecution]:
        """Parse multiple comments and return all pipeline executions"""
        executions = []

        for comment in comments:
            body = comment.get('body', '')
            pr_number = comment.get('pr_number')
            pr_url = comment.get('pr_url')
            comment_id = comment.get('id')

            execution = self.parse_pipeline_summary(
                body, pr_number, pr_url, comment_id, repository
            )

            if execution:
                executions.append(execution)

        return executions

    def _extract_pipelinerun_name(self, comment_body: str) -> Optional[str]:
        """Extract PipelineRun name from comment"""
        match = self.pipelinerun_name_pattern.search(comment_body)
        if match:
            return match.group(1).strip()
        return None

    def _extract_start_time(self, comment_body: str) -> Optional[datetime]:
        """Extract pipeline start time from comment"""
        match = self.start_time_pattern.search(comment_body)
        if match:
            time_str = match.group(1).strip()
            try:
                # Try to parse ISO format datetime
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            except ValueError:
                # Try alternative formats
                formats = [
                    "%Y-%m-%d %H:%M:%S%z",
                    "%Y-%m-%d %H:%M:%S+00:00",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%SZ"
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(time_str, fmt)
                    except ValueError:
                        continue
        return None

    def _extract_pipeline_logs_url(self, comment_body: str) -> Optional[str]:
        """Extract pipeline logs URL from comment"""
        match = self.pipeline_logs_pattern.search(comment_body)
        if match:
            return match.group(1).strip()
        return None

    def _extract_troubleshooting_guide_url(self, comment_body: str) -> Optional[str]:
        """Extract troubleshooting guide URL from comment"""
        match = self.troubleshooting_guide_pattern.search(comment_body)
        if match:
            return match.group(1).strip()
        return None

    def _extract_restart_command(self, comment_body: str) -> Optional[str]:
        """Extract restart command from comment"""
        match = self.restart_command_pattern.search(comment_body)
        if match:
            return match.group(1).strip()
        return None

    def _extract_tasks_from_table(self, comment_body: str) -> List[TaskExecution]:
        """Extract task information from table format"""
        tasks = []

        # Look for table format tasks
        lines = comment_body.split('\n')
        in_table = False

        for line in lines:
            line = line.strip()

            # Check if we're in a table (look for table header separator)
            if re.match(r'\|\s*-+\s*\|\s*-+\s*\|\s*-+\s*\|\s*-+\s*\|', line):
                in_table = True
                continue

            # Skip table header
            if 'Status' in line and 'Task' in line and 'Start Time' in line:
                continue

            # Parse table rows
            if in_table and line.startswith('|') and line.endswith('|'):
                parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove empty first and last

                if len(parts) >= 4:
                    status_str = parts[0]
                    task_name = parts[1]
                    start_time_str = parts[2]
                    duration_str = parts[3]

                    # Map status
                    status = self.status_mapping.get(status_str, TaskStatus.UNKNOWN)

                    # Parse start time
                    task_start_time = None
                    if start_time_str and start_time_str != '-':
                        try:
                            task_start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        except ValueError:
                            pass

                    # Clean up duration
                    duration = duration_str if duration_str and duration_str != '-' else None

                    # Create task execution
                    task = TaskExecution(
                        name=task_name,
                        status=status,
                        duration=duration,
                        start_time=task_start_time
                    )
                    tasks.append(task)
            elif in_table and not line.startswith('|'):
                # End of table
                break

        return tasks
