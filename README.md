# GitHub PR Pipeline Parser

A comprehensive tool to parse Tekton pipeline summaries from GitHub Pull Request comments and generate statistics about pipeline performance across repositories.

## Features

- 🔍 **Parse Pipeline Summaries**: Extracts Tekton pipeline information from GitHub PR comments
- 📊 **Statistics Generation**: Tracks success rates, execution counts, and task-level metrics
- 🏢 **Multi-Repository Support**: Works with any GitHub repository
- 💾 **Local Storage**: Stores statistics in JSON format for easy analysis
- 🎨 **Rich CLI Interface**: Beautiful command-line interface with progress bars and tables
- 📈 **Export Capabilities**: Export statistics to JSON for further analysis

## Installation

1. Clone or download the project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your GitHub token (see Setup section below)

## Quick Start

### 1. Setup
Run the interactive setup to configure your GitHub token:

```bash
python main.py setup
```

### 2. Parse Pipeline Comments
Parse pipeline summaries from a specific repository:

```bash
python main.py parse owner/repo-name
```

### 3. View Statistics
View overall statistics:

```bash
python main.py stats
```

View statistics for a specific pipeline:

```bash
python main.py stats --pipeline "my-pipeline-name"
```

## Commands

### `parse` - Parse Pipeline Summaries

Parse pipeline summaries from GitHub PR comments.

```bash
python main.py parse REPOSITORY [OPTIONS]
```

**Arguments:**
- `REPOSITORY`: GitHub repository in format 'owner/repo'

**Options:**
- `--pr INTEGER`: Specific PR number to parse
- `--limit INTEGER`: Maximum number of PRs to check (default: 50)
- `--days INTEGER`: Number of days back to search (default: 30)
- `--max-prs INTEGER`: Maximum number of PRs to fetch initially (default: 500)
- `--data-dir TEXT`: Directory to store statistics (default: data)
- `--token TEXT`: GitHub token (or set GITHUB_TOKEN env var)

**Examples:**
```bash
# Parse recent PRs from a repository
python main.py parse kubernetes/kubernetes

# Parse a specific PR
python main.py parse kubernetes/kubernetes --pr 12345

# Parse last 100 PRs from the last 7 days, fetching max 1000 PRs initially
python main.py parse kubernetes/kubernetes --limit 100 --days 7 --max-prs 1000

# For very large repositories, limit initial PR fetch to 200
python main.py parse kubernetes/kubernetes --max-prs 200
```

### `stats` - View Statistics

Display pipeline statistics with filtering options.

```bash
python main.py stats [OPTIONS]
```

**Options:**
- `--pipeline TEXT`: Show stats for specific pipeline
- `--repository TEXT`: Filter by repository (e.g., 'owner/repo')
- `--status TEXT`: Filter by status (success/failed/etc.)
- `--show-tasks`: Show task statistics
- `--min-executions INTEGER`: Minimum number of executions to show (default: 1)
- `--data-dir TEXT`: Directory with statistics data (default: data)

**Examples:**
```bash
# Show overall statistics
python main.py stats

# Show specific pipeline statistics with tasks
python main.py stats --pipeline "ci-pipeline" --show-tasks

# Filter by repository
python main.py stats --repository "kubernetes/kubernetes"

# Show only pipelines with failed status
python main.py stats --status failed

# Show pipelines with at least 10 executions from specific repository
python main.py stats --repository "tektoncd/pipeline" --min-executions 10 --show-tasks

# Combine multiple filters
python main.py stats --repository "owner/repo" --status success --min-executions 5
```

### `tasks` - View Task Statistics

Show task statistics across all pipelines with filtering options.

```bash
python main.py tasks [OPTIONS]
```

**Options:**
- `--task TEXT`: Show stats for specific task
- `--repository TEXT`: Filter by repository (e.g., 'owner/repo')
- `--pipeline TEXT`: Filter by pipeline name
- `--min-executions INTEGER`: Minimum number of executions to show (default: 1)
- `--data-dir TEXT`: Directory with statistics data (default: data)

**Examples:**
```bash
# Show all task statistics
python main.py tasks

# Show specific task details
python main.py tasks --task "build-image"

# Show tasks from specific repository
python main.py tasks --repository "kubernetes/kubernetes"

# Show tasks from specific pipeline
python main.py tasks --pipeline "ci-pipeline"

# Show tasks with at least 5 executions
python main.py tasks --min-executions 5

# Combine filters - tasks from specific pipeline in specific repository
python main.py tasks --repository "tektoncd/pipeline" --pipeline "tekton-ci" --min-executions 3
```

### `list-executions` - List Recent Executions

List recent pipeline executions with filtering options.

```bash
python main.py list-executions [OPTIONS]
```

**Options:**
- `--pipeline TEXT`: Filter by pipeline name
- `--repository TEXT`: Filter by repository
- `--status TEXT`: Filter by status (success/failed/etc.)
- `--limit INTEGER`: Maximum number of executions to show (default: 10)
- `--data-dir TEXT`: Directory with statistics data (default: data)

**Examples:**
```bash
# List recent executions
python main.py list-executions

# List failed executions
python main.py list-executions --status failed

# List executions for specific pipeline
python main.py list-executions --pipeline "my-pipeline"
```

### `export` - Export Statistics

Export statistics to JSON file.

```bash
python main.py export [OPTIONS]
```

**Options:**
- `--filename TEXT`: Export filename (auto-generated if not specified)
- `--data-dir TEXT`: Directory with statistics data (default: data)

### `test-parser` - Test Parser

Test the parser with a sample comment file.

```bash
python main.py test-parser COMMENT_FILE
```

**Arguments:**
- `COMMENT_FILE`: Path to file containing a sample comment

### `setup` - Interactive Setup

Run interactive setup for GitHub token and configuration.

```bash
python main.py setup
```

### `logs` - View Pipeline Log URLs

Show pipeline log URLs with filtering options for debugging and troubleshooting.

```bash
python main.py logs [OPTIONS]
```

**Options:**
- `--task TEXT`: Filter by specific task name
- `--pipeline TEXT`: Filter by pipeline name
- `--repository TEXT`: Filter by repository (e.g., 'owner/repo')
- `--status TEXT`: Filter by pipeline status (success/failed/etc.)
- `--task-status TEXT`: Filter by task status (success/failed/etc.)
- `--limit INTEGER`: Maximum number of logs to show (default: 20)
- `--data-dir TEXT`: Directory with statistics data (default: data)

**Examples:**
```bash
# Show recent pipeline logs
python main.py logs

# Show logs for all failed tasks
python main.py logs --task-status failed

# Show logs for specific task across all pipelines
python main.py logs --task "build-image"

# Show logs for failed pipelines in specific repository
python main.py logs --repository "kubernetes/kubernetes" --status failed

# Debug specific task failures
python main.py logs --task "security-scan" --task-status failed --limit 10

# Show logs for specific pipeline
python main.py logs --pipeline "ci-pipeline" --limit 5

# Complex debugging - failed tasks in specific pipeline and repository
python main.py logs --repository "tektoncd/pipeline" --pipeline "tekton-ci" --task-status failed
```

## Setup

### GitHub Token

You need a GitHub Personal Access Token to use this tool:

1. Go to https://github.com/settings/tokens
2. Create a new token with these permissions:
   - For public repositories: `public_repo`
   - For private repositories: `repo`
3. Set the token as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```
   Or save it in a `.env` file:
   ```
   GITHUB_TOKEN=your_token_here
   ```

### Environment Variables

Create a `.env` file in the project directory:

```
GITHUB_TOKEN=your_github_token_here
```

## Pipeline Summary Format

The parser recognizes pipeline summaries that start with "Pipeline Summary" heading. Here's an example format:

```markdown
# Pipeline Summary

Pipeline: `my-tekton-pipeline`
Success Rate: 85.7%
Duration: 15m 30s

## Task Status
- build-image: ✅ (2m 15s)
- run-tests: ✅ (5m 45s)
- security-scan: ❌ (timeout)
- deploy: ⏭️ (skipped)
```

### Supported Status Symbols

- ✅ Success
- ❌ Failed
- ⏭️ Skipped
- 🔄 Running
- ⏸️ Pending
- ❓ Unknown

## Data Storage

Statistics are stored locally in JSON format:
- `data/pipeline_stats.json`: Main statistics database
- Statistics include:
  - Pipeline execution counts and success rates
  - Task-level statistics
  - Repository tracking
  - Execution history

## Examples

### Example 1: Parse Recent PRs

```bash
# Parse recent PRs from OpenShift operator repository
python main.py parse openshift/cluster-monitoring-operator

# View the statistics
python main.py stats
```

### Example 2: Monitor Specific Pipeline

```bash
# Parse PRs and focus on a specific pipeline
python main.py parse tektoncd/pipeline --limit 100
python main.py stats --pipeline "tekton-pipeline-ci" --show-tasks

# Analyze task failures in that pipeline
python main.py tasks --pipeline "tekton-pipeline-ci" --min-executions 3
```

### Example 3: Repository Analysis with Filtering

```bash
# Parse multiple repositories
python main.py parse kubernetes/kubernetes --max-prs 300
python main.py parse openshift/origin --max-prs 200

# Compare performance across repositories
python main.py stats --repository "kubernetes/kubernetes" --show-tasks
python main.py stats --repository "openshift/origin" --show-tasks

# Focus on problematic areas
python main.py stats --status failed --min-executions 5
python main.py tasks --min-executions 10

# Get logs for debugging failed tasks
python main.py logs --task-status failed --limit 15
python main.py logs --task "integration-tests" --task-status failed

# Export combined statistics
python main.py export --filename combined_stats.json
```

## Supported Pipeline Summary Formats

The parser is flexible and can handle various formats:

### Format 1: Basic Format
```markdown
# Pipeline Summary
Pipeline: my-pipeline
Success Rate: 90%
- task1: ✅
- task2: ❌
- task3: ✅
```

### Format 2: Detailed Format
```markdown
# Pipeline Summary

**Pipeline**: `ci-pipeline`
**Success Rate**: 75.0%
**Duration**: 25m 12s

## Tasks
- build: ✅ (3m 45s)
- test: ❌ (failed with error)
- deploy: ⏭️
```

### Format 3: Table Format
```markdown
# Pipeline Summary

| Task | Status | Duration |
|------|--------|----------|
| build | ✅ | 5m 20s |
| test | ✅ | 10m 15s |
| deploy | ❌ | 2m 30s |
```

## Architecture

The tool consists of several components:

- **`models.py`**: Pydantic data models for type safety
- **`parser.py`**: Pipeline summary parsing logic
- **`github_client.py`**: GitHub API interaction
- **`stats_manager.py`**: Statistics management and persistence
- **`main.py`**: CLI interface and command handling

## Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**
   - Check your rate limit: The tool shows remaining API calls
   - Wait for the rate limit to reset
   - Use a different token if needed

2. **No Pipeline Comments Found**
   - Verify the repository name format: `owner/repo`
   - Check if the repository has PRs with pipeline comments
   - Increase the `--days` parameter to search further back

3. **Token Authentication Failed**
   - Verify your token has the correct permissions
   - Check if the token is expired
   - Ensure the token is correctly set in environment variables

### Debug Mode

For debugging, you can test the parser with sample comments:

```bash
# Create a sample comment file
echo "# Pipeline Summary
Pipeline: test-pipeline
- task1: ✅
- task2: ❌" > sample_comment.txt

# Test the parser
python main.py test-parser sample_comment.txt
```

## Filtering and Analysis

### Advanced Filtering Options

The tool provides powerful filtering capabilities to analyze specific subsets of your pipeline data:

#### Repository Filtering
Focus on pipelines from specific repositories:
```bash
# Analyze only kubernetes/kubernetes pipelines
python main.py stats --repository "kubernetes/kubernetes"

# Show task performance across tektoncd repositories
python main.py tasks --repository "tektoncd/pipeline"
```

#### Pipeline Filtering
Analyze specific pipeline performance:
```bash
# Deep dive into a specific pipeline
python main.py stats --pipeline "ci-pipeline" --show-tasks

# Compare task performance across a specific pipeline
python main.py tasks --pipeline "integration-tests"
```

#### Status Filtering
Focus on failed pipelines for troubleshooting:
```bash
# Find all failed pipeline executions
python main.py stats --status failed

# Analyze patterns in failed executions
python main.py list-executions --status failed --limit 20
```

#### Execution Volume Filtering
Filter out low-volume pipelines for better analysis:
```bash
# Show only active pipelines (10+ executions)
python main.py stats --min-executions 10 --show-tasks

# Focus on frequently failing tasks
python main.py tasks --min-executions 5
```

#### Combined Filtering
Combine multiple filters for targeted analysis:
```bash
# Analyze failed pipelines in specific repository
python main.py stats --repository "kubernetes/kubernetes" --status failed

# Deep analysis of specific pipeline in specific repo
python main.py stats --repository "tektoncd/pipeline" --pipeline "tekton-ci" --show-tasks --min-executions 5

# Task analysis with multiple filters
python main.py tasks --repository "owner/repo" --pipeline "ci-pipeline" --min-executions 3
```

### Use Cases for Filtering

**Troubleshooting**: `--status failed --repository "my-org/my-repo"`
**Performance Analysis**: `--min-executions 10 --show-tasks`
**Repository Comparison**: Multiple commands with different `--repository` filters
**Pipeline Health Check**: `--pipeline "critical-pipeline" --show-tasks`
**Task Reliability**: `--task "deploy" --min-executions 5`

## Debugging Workflows

### Troubleshooting Failed Pipelines

**Step 1: Identify Problem Areas**
```bash
# Find pipelines with high failure rates
python main.py stats --status failed --min-executions 5

# Identify most problematic tasks
python main.py tasks --min-executions 5
```

**Step 2: Get Specific Log URLs**
```bash
# Get logs for all failed pipelines in a repository
python main.py logs --repository "my-org/repo" --status failed

# Focus on specific failing task
python main.py logs --task "integration-tests" --task-status failed --limit 10
```

**Step 3: Deep Dive Analysis**
```bash
# Analyze task patterns for specific pipeline
python main.py stats --pipeline "problematic-pipeline" --show-tasks

# Get recent logs for debugging
python main.py logs --pipeline "problematic-pipeline" --task-status failed
```

### Performance Investigation

**Step 1: Find Slow Tasks**
```bash
# Find tasks that frequently fail or skip
python main.py tasks --repository "kubernetes/kubernetes" --min-executions 10
```

**Step 2: Get Execution Details**
```bash
# Get recent executions of slow tasks
python main.py logs --task "build-image" --limit 15

# Check specific pipeline performance
python main.py logs --pipeline "nightly-builds" --limit 20
```

### Cross-Repository Analysis

**Step 1: Compare Repositories**
```bash
# Compare task success rates across repositories
python main.py tasks --repository "tektoncd/pipeline" --min-executions 5
python main.py tasks --repository "kubernetes/kubernetes" --min-executions 5
```

**Step 2: Get Comparative Log Access**
```bash
# Get logs for same task across different repositories
python main.py logs --task "security-scan" --repository "tektoncd/pipeline"
python main.py logs --task "security-scan" --repository "kubernetes/kubernetes"
```

## Performance Optimizations

### PR Fetching Limits

For large repositories with thousands of PRs, the tool includes several optimizations:

- **`--max-prs`**: Limits the initial number of PRs fetched (default: 500)
- **Date Filtering**: Only processes PRs updated within the specified timeframe
- **Batch Processing**: Efficiently processes comments in batches
- **Progress Tracking**: Clear progress indicators for each stage

### Recommended Settings by Repository Size

**Small Repositories** (< 100 PRs):
```bash
python main.py parse small-org/repo --max-prs 100
```

**Medium Repositories** (100-1000 PRs):
```bash
python main.py parse medium-org/repo --max-prs 500 --limit 50
```

**Large Repositories** (1000+ PRs like kubernetes/kubernetes):
```bash
python main.py parse kubernetes/kubernetes --max-prs 300 --limit 25 --days 14
```

### API Rate Limits

The tool respects GitHub API rate limits:
- **5,000 requests/hour** for authenticated requests
- **60 requests/hour** for unauthenticated requests
- Use `--max-prs` to control API usage for large repositories

## Data Storage

Statistics are stored locally in JSON format:
- `data/pipeline_stats.json`: Main statistics database
- Statistics include:
  - Pipeline execution counts and success rates
  - Task-level statistics
  - Repository tracking
  - Execution history
