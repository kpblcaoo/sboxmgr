#!/usr/bin/env python3
"""Monitor CI checks and bot comments after push.

This script waits for CI checks to complete and monitors for bot comments
on the latest commit. Useful for automated monitoring after pushing changes.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import requests


class GitHubMonitor:
    """Monitor GitHub CI checks and bot comments."""

    def __init__(self, repo_owner: str, repo_name: str, token: Optional[str] = None):
        """Initialize GitHub monitor.

        Args:
            repo_owner: Repository owner (username or organization)
            repo_name: Repository name
            token: GitHub personal access token (optional, for private repos)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "sboxmgr-ci-monitor",
        }

        if token:
            self.headers["Authorization"] = f"token {token}"
        elif os.getenv("GITHUB_TOKEN"):
            self.headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"

    def get_latest_commit_sha(self, branch: str = "main") -> Optional[str]:
        """Get the latest commit SHA for a branch.

        Args:
            branch: Branch name (default: main)

        Returns:
            Commit SHA or None if not found
        """
        url = (
            f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{branch}"
        )

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["sha"]
        except requests.RequestException as e:
            print(f"Error getting latest commit: {e}")
            return None

    def get_commit_checks(self, commit_sha: str) -> list[dict[str, Any]]:
        """Get CI checks for a commit.

        Args:
            commit_sha: Commit SHA

        Returns:
            List of check runs
        """
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{commit_sha}/check-runs"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()["check_runs"]
        except requests.RequestException as e:
            print(f"Error getting commit checks: {e}")
            return []

    def get_commit_comments(self, commit_sha: str) -> list[dict[str, Any]]:
        """Get comments on a commit.

        Args:
            commit_sha: Commit SHA

        Returns:
            List of comments
        """
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/commits/{commit_sha}/comments"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting commit comments: {e}")
            return []

    def get_check_run_logs_url(self, check_run: dict) -> Optional[str]:
        """Get the logs URL for a check run (if available)."""
        # For GitHub Actions, logs_url is available
        if "logs_url" in check_run:
            return check_run["logs_url"]
        # For other checks, details_url is the best we can do
        return check_run.get("details_url")

    def print_failed_check_logs(self, check_runs: list[dict[str, Any]]):
        """Print logs for all failed/neutral check runs (if possible)."""
        for check in check_runs:
            name = check.get("name", "Unknown")
            status = check.get("status", "unknown")
            conclusion = check.get("conclusion")
            if conclusion not in ("success", None):
                print(
                    f"\n🔴 CI check failed or not green: {name} (status={status}, conclusion={conclusion})"
                )
                logs_url = self.get_check_run_logs_url(check)
                if logs_url:
                    print(f"  📄 Logs/details: {logs_url}")
                    # Try to fetch logs if it's a raw logs_url (GitHub Actions)
                    if logs_url.endswith("/logs"):
                        try:
                            resp = requests.get(logs_url, headers=self.headers)
                            if resp.status_code == 200:
                                print("  --- CI LOG START ---")
                                print(resp.text[:5000])  # Print first 5000 chars
                                if len(resp.text) > 5000:
                                    print("  ... (truncated) ...")
                                print("  --- CI LOG END ---")
                            else:
                                print(
                                    f"  (Could not fetch raw log, status {resp.status_code})"
                                )
                        except Exception as e:
                            print(f"  (Error fetching log: {e})")
                else:
                    print("  (No logs_url/details_url available)")

    def print_bot_comments(
        self, commit_sha: str, bot_names=("bugbot", "cursor-bugbot", "Cursor BugBot")
    ):
        """Print comments from BugBot or other bots on a commit."""
        comments = self.get_commit_comments(commit_sha)
        found = False
        for comment in comments:
            user = comment.get("user", {}).get("login", "").lower()
            if any(bot in user for bot in bot_names) or any(
                bot in comment.get("user", {}).get("login", "") for bot in bot_names
            ):
                found = True
                print(
                    f"\n🤖 Bot comment by {comment.get('user', {}).get('login', 'Unknown')}:\n{'-' * 40}"
                )
                print(comment.get("body", "")[:2000])
                if len(comment.get("body", "")) > 2000:
                    print("... (truncated) ...")
                print("\nLink: " + comment.get("html_url", "(no url)"))
        if not found:
            print("(No bot comments found)")

    def wait_for_ci_completion(
        self, commit_sha: str, timeout_minutes: int = 10
    ) -> bool:
        """Wait for CI checks to complete. Also print logs for failed/neutral checks."""
        print(f"🔍 Monitoring CI checks for commit {commit_sha[:8]}...")

        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)

        last_check_runs = []
        while datetime.now() - start_time < timeout:
            checks = self.get_commit_checks(commit_sha)
            last_check_runs = checks
            if not checks:
                print("⏳ No CI checks found yet, waiting...")
                time.sleep(30)
                continue

            completed = 0
            failed = 0
            pending = 0
            non_green = 0
            bugbot_status = None
            for check in checks:
                status = check.get("status", "unknown")
                conclusion = check.get("conclusion")
                name = check.get("name", "Unknown")
                if name.lower().startswith("cursor bugbot"):
                    bugbot_status = conclusion
                if status == "completed":
                    completed += 1
                    if conclusion == "failure":
                        failed += 1
                        non_green += 1
                        print(f"❌ {name}: FAILED")
                    elif conclusion == "success":
                        print(f"✅ {name}: PASSED")
                    elif conclusion == "neutral":
                        non_green += 1
                        print(f"⚠️  {name}: NEUTRAL")
                    else:
                        non_green += 1
                        print(f"⚠️  {name}: {conclusion}")
                else:
                    pending += 1
                    print(f"⏳ {name}: {status}")
            print(
                f"📊 Status: {completed} completed, {pending} pending, {failed} failed, {non_green} non-green"
            )
            # If all checks completed
            if pending == 0:
                if non_green == 0:
                    print("🎉 All CI checks passed!")
                    return True
                else:
                    print("💥 Some CI checks failed or are not green!")
                    # Print logs for failed/neutral checks
                    self.print_failed_check_logs(last_check_runs)
                    # Print BugBot comments if BugBot is not green
                    if bugbot_status and bugbot_status != "success":
                        print("\n--- BugBot status is not green, reading comments ---")
                        self.print_bot_comments(commit_sha)
                    return False
            time.sleep(30)
        print(f"⏰ Timeout after {timeout_minutes} minutes")
        # On timeout, print logs/comments if any non-green
        self.print_failed_check_logs(last_check_runs)
        if bugbot_status and bugbot_status != "success":
            print("\n--- BugBot status is not green, reading comments ---")
            self.print_bot_comments(commit_sha)
        return False

    def monitor_bot_comments(
        self, commit_sha: str, timeout_minutes: int = 5
    ) -> list[dict[str, Any]]:
        """Monitor for bot comments on a commit.

        Args:
            commit_sha: Commit SHA to monitor
            timeout_minutes: Maximum time to wait in minutes

        Returns:
            List of bot comments found
        """
        print(f"🤖 Monitoring for bot comments on commit {commit_sha[:8]}...")

        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        initial_comments = set()

        # Get initial comments
        comments = self.get_commit_comments(commit_sha)
        for comment in comments:
            comment_id = comment.get("id")
            if comment_id:
                initial_comments.add(comment_id)

        while datetime.now() - start_time < timeout:
            comments = self.get_commit_comments(commit_sha)
            new_comments = []

            for comment in comments:
                comment_id = comment.get("id")
                if comment_id and comment_id not in initial_comments:
                    new_comments.append(comment)

            if new_comments:
                print(f"📝 Found {len(new_comments)} new comment(s):")
                for comment in new_comments:
                    user = comment.get("user", {}).get("login", "Unknown")
                    body = (
                        comment.get("body", "")[:100] + "..."
                        if len(comment.get("body", "")) > 100
                        else comment.get("body", "")
                    )
                    print(f"  👤 {user}: {body}")
                return new_comments

            print("⏳ No new bot comments yet, waiting...")
            time.sleep(30)

        print("⏰ No new bot comments found within timeout")
        return []


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor CI checks and bot comments")
    parser.add_argument("--owner", default="kpblcaoo", help="Repository owner")
    parser.add_argument("--repo", default="sboxmgr", help="Repository name")
    parser.add_argument(
        "--branch", default="chore/ci-critical-import-checks", help="Branch to monitor"
    )
    parser.add_argument("--commit", help="Specific commit SHA to monitor")
    parser.add_argument(
        "--ci-timeout", type=int, default=10, help="CI timeout in minutes"
    )
    parser.add_argument(
        "--bot-timeout", type=int, default=5, help="Bot monitoring timeout in minutes"
    )
    parser.add_argument("--token", help="GitHub personal access token")

    args = parser.parse_args()

    # Initialize monitor
    monitor = GitHubMonitor(args.owner, args.repo, args.token)

    # Get commit SHA
    if args.commit:
        commit_sha = args.commit
    else:
        commit_sha = monitor.get_latest_commit_sha(args.branch)
        if not commit_sha:
            print("❌ Could not get latest commit SHA")
            sys.exit(1)

    print(
        f"🚀 Starting monitoring for commit {commit_sha[:8]} on {args.owner}/{args.repo}"
    )

    # Wait for CI completion
    ci_success = monitor.wait_for_ci_completion(commit_sha, args.ci_timeout)

    if not ci_success:
        print("❌ CI checks failed or timed out")
        sys.exit(1)

    # Monitor for bot comments
    bot_comments = monitor.monitor_bot_comments(commit_sha, args.bot_timeout)

    if bot_comments:
        print(f"🤖 Found {len(bot_comments)} bot comment(s)")
        # Save comments to file for further processing
        with open("bot_comments.json", "w") as f:
            json.dump(bot_comments, f, indent=2)
        print("💾 Bot comments saved to bot_comments.json")
    else:
        print("🤖 No bot comments found")

    print("✅ Monitoring completed")


if __name__ == "__main__":
    main()
