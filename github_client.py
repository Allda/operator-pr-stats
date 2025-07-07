"""
GitHub API client for fetching PR comments
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from github import Github, GithubException
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class GitHubClient:
    """Client for interacting with GitHub API"""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client

        Args:
            token: GitHub personal access token. If not provided, will look for GITHUB_TOKEN env var
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass token parameter")

        self.github = Github(self.token)
        self.console = Console()

    def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """Get basic repository information"""
        try:
            repo = self.github.get_repo(repo_name)
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'url': repo.html_url,
                'open_issues': repo.open_issues_count,
                'stargazers': repo.stargazers_count,
                'forks': repo.forks_count,
            }
        except GithubException as e:
            self.console.print(f"[red]Error fetching repository info: {e}[/red]")
            return {}

    def get_pr_comments(self, repo_name: str, pr_number: Optional[int] = None,
                       limit: int = 100, days_back: int = 30, max_prs: int = 500) -> List[Dict[str, Any]]:
        """
        Get PR comments from a repository

        Args:
            repo_name: Repository name in format "owner/repo"
            pr_number: Specific PR number to fetch comments from (optional)
            limit: Maximum number of comments to fetch
            days_back: Number of days back to search for comments
            max_prs: Maximum number of PRs to fetch initially

        Returns:
            List of comment dictionaries
        """
        try:
            repo = self.github.get_repo(repo_name)
            comments = []

            if pr_number:
                # Get comments from specific PR
                comments.extend(self._get_pr_comments(repo, pr_number))
            else:
                # Get comments from recent PRs
                comments.extend(self._get_recent_pr_comments(repo, limit, days_back, max_prs))

            return comments

        except GithubException as e:
            self.console.print(f"[red]Error fetching PR comments: {e}[/red]")
            return []

    def _get_pr_comments(self, repo, pr_number: int) -> List[Dict[str, Any]]:
        """Get regular comments from a specific PR (excluding review comments)"""
        comments = []

        try:
            pr = repo.get_pull(pr_number)

            # Get issue comments (regular PR comments only)
            issue_comments = list(pr.get_issue_comments())
            for comment in issue_comments:
                comments.append({
                    'id': comment.id,
                    'body': comment.body,
                    'author': comment.user.login,
                    'created_at': comment.created_at,
                    'updated_at': comment.updated_at,
                    'pr_number': pr_number,
                    'pr_url': pr.html_url,
                    'pr_title': pr.title,
                    'pr_state': pr.state,
                    'type': 'issue_comment'
                })

            if len(issue_comments) > 0:
                self.console.print(f"[dim]  • Found {len(issue_comments)} comments[/dim]")

        except GithubException as e:
            self.console.print(f"[red]Error fetching comments from PR #{pr_number}: {e}[/red]")

        return comments

    def _get_recent_pr_comments(self, repo, limit: int, days_back: int, max_prs_to_fetch: int = 500) -> List[Dict[str, Any]]:
        """Get comments from recent PRs"""
        comments = []
        cutoff_date = datetime.now().replace(tzinfo=None) - \
                     timedelta(days=days_back)

        try:
            self.console.print(f"[blue]📡 Fetching recent PRs (max: {max_prs_to_fetch}, looking for {limit} within {days_back} days)[/blue]")

            # Get recent PRs (both open and closed) - limit the initial fetch
            prs_paginated = repo.get_pulls(state='all', sort='updated', direction='desc')
            prs = []

            # Fetch PRs in batches, up to max_prs_to_fetch
            for i, pr in enumerate(prs_paginated):
                if i >= max_prs_to_fetch:
                    break
                prs.append(pr)

            self.console.print(f"[blue]📄 Fetched {len(prs)} PRs, filtering by date and limit[/blue]")

            # Filter PRs by date first
            recent_prs = []
            for pr in prs:
                if len(recent_prs) >= limit:
                    break

                pr_updated = pr.updated_at.replace(tzinfo=None) if pr.updated_at else datetime.min
                if pr_updated >= cutoff_date:
                    recent_prs.append(pr)

            self.console.print(f"[green]✅ Found {len(recent_prs)} recent PRs to process[/green]")

            if not recent_prs:
                return comments

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=False
            ) as progress:
                pr_task = progress.add_task("Processing PRs...", total=len(recent_prs))

                for pr in recent_prs:
                    progress.update(pr_task, description=f"Processing PR #{pr.number}: {pr.title[:50]}...")

                    # Get comments from this PR
                    pr_comments = self._get_pr_comments(repo, pr.number)

                    # Filter comments by date
                    recent_comments = [
                        comment for comment in pr_comments
                        if comment['created_at'].replace(tzinfo=None) >= cutoff_date
                    ]

                    comments.extend(recent_comments)
                    progress.advance(pr_task)

        except GithubException as e:
            self.console.print(f"[red]Error fetching recent PRs: {e}[/red]")

        return comments

    def search_pipeline_comments(self, repo_name: str, search_terms: List[str] = None,
                            limit: int = 100, days_back: int = 30, max_prs: int = 500) -> List[Dict[str, Any]]:
        """
        Search for comments containing pipeline summaries

        Args:
            repo_name: Repository name in format "owner/repo"
            search_terms: List of terms to search for (defaults to pipeline-related terms)
            limit: Maximum number of comments to fetch
            days_back: Number of days back to search
            max_prs: Maximum number of PRs to fetch initially

        Returns:
            List of comments containing pipeline summaries
        """
        if search_terms is None:
            search_terms = ['Pipeline Summary', 'Tekton', 'pipeline', 'Task Status']

        self.console.print(f"[blue]🔍 Searching for pipeline comments in {repo_name}[/blue]")
        all_comments = self.get_pr_comments(repo_name, limit=limit, days_back=days_back, max_prs=max_prs)

        if not all_comments:
            return []

        self.console.print(f"[blue]📝 Filtering {len(all_comments)} comments for pipeline summaries[/blue]")

        # Filter comments that contain pipeline summaries
        pipeline_comments = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=False
        ) as progress:
            filter_task = progress.add_task("Filtering comments...", total=len(all_comments))

            for comment in all_comments:
                body = comment.get('body', '').lower()
                if any(term.lower() in body for term in search_terms):
                    pipeline_comments.append(comment)
                progress.advance(filter_task)

        self.console.print(f"[green]✅ Found {len(pipeline_comments)} pipeline comments[/green]")
        return pipeline_comments

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                'core': {
                    'limit': rate_limit.core.limit,
                    'remaining': rate_limit.core.remaining,
                    'reset': rate_limit.core.reset
                },
                'search': {
                    'limit': rate_limit.search.limit,
                    'remaining': rate_limit.search.remaining,
                    'reset': rate_limit.search.reset
                }
            }
        except GithubException as e:
            self.console.print(f"[red]Error fetching rate limit: {e}[/red]")
            return {}
