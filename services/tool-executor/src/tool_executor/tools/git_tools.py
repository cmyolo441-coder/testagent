"""Git Tools — Git operations for version control"""
import subprocess
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class GitResult:
    success: bool
    output: str
    error: str
    command: str
    return_code: int

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output[:2000],
            "error": self.error[:500],
            "command": self.command,
            "return_code": self.return_code,
        }


class GitTools:
    """Git operations for version control."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def status(self,porcelain: bool = True) -> GitResult:
        cmd = ["git", "status"]
        if porcelain:
            cmd.append("--porcelain")
        return self._run(cmd)

    def diff(self, target: str = "HEAD", staged: bool = False,
             file_path: str = "") -> GitResult:
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        cmd.append(target)
        if file_path:
            cmd.append(file_path)
        return self._run(cmd)

    def log(self, count: int = 10, oneline: bool = True,
            author: str = "", since: str = "") -> GitResult:
        cmd = ["git", "log", f"-{count}"]
        if oneline:
            cmd.append("--oneline")
        if author:
            cmd.extend(["--author", author])
        if since:
            cmd.extend(["--since", since])
        return self._run(cmd)

    def commit(self, message: str, files: list[str] = None,
               amend: bool = False) -> GitResult:
        if files:
            for f in files:
                self._run(["git", "add", f])
        else:
            self._run(["git", "add", "-A"])

        cmd = ["git", "commit", "-m", message]
        if amend:
            cmd.append("--amend")
        return self._run(cmd)

    def push(self, remote: str = "origin", branch: str = "",
             force: bool = False, set_upstream: bool = False) -> GitResult:
        cmd = ["git", "push", remote]
        if branch:
            cmd.append(branch)
        if force:
            cmd.append("--force-with-lease")
        if set_upstream:
            cmd.append("-u")
        return self._run(cmd)

    def pull(self, remote: str = "origin", branch: str = "",
             rebase: bool = False) -> GitResult:
        cmd = ["git", "pull", remote]
        if branch:
            cmd.append(branch)
        if rebase:
            cmd.append("--rebase")
        return self._run(cmd)

    def checkout(self, branch: str, create: bool = False) -> GitResult:
        cmd = ["git", "checkout"]
        if create:
            cmd.append("-b")
        cmd.append(branch)
        return self._run(cmd)

    def branch(self, list_all: bool = False, branch_name: str = "") -> GitResult:
        cmd = ["git", "branch"]
        if list_all:
            cmd.append("-a")
        if branch_name:
            cmd.append(branch_name)
        return self._run(cmd)

    def merge(self, branch: str, message: str = "") -> GitResult:
        cmd = ["git", "merge", branch]
        if message:
            cmd.extend(["-m", message])
        return self._run(cmd)

    def stash(self, message: str = "") -> GitResult:
        cmd = ["git", "stash"]
        if message:
            cmd.extend(["push", "-m", message])
        return self._run(cmd)

    def stash_pop(self) -> GitResult:
        return self._run(["git", "stash", "pop"])

    def tag(self, tag_name: str = "", message: str = "") -> GitResult:
        if tag_name:
            cmd = ["git", "tag", tag_name]
            if message:
                cmd.extend(["-m", message])
            return self._run(cmd)
        return self._run(["git", "tag"])

    def remote(self, verbose: bool = False) -> GitResult:
        cmd = ["git", "remote"]
        if verbose:
            cmd.append("-v")
        return self._run(cmd)

    def blame(self, file_path: str) -> GitResult:
        return self._run(["git", "blame", file_path])

    def show(self, commit: str = "HEAD", stat: bool = True) -> GitResult:
        cmd = ["git", "show", commit]
        if stat:
            cmd.append("--stat")
        return self._run(cmd)

    def init(self, bare: bool = False) -> GitResult:
        cmd = ["git", "init"]
        if bare:
            cmd.append("--bare")
        return self._run(cmd)

    def clone(self, url: str, target: str = "") -> GitResult:
        cmd = ["git", "clone", url]
        if target:
            cmd.append(target)
        return self._run(cmd)

    def _run(self, cmd: list[str]) -> GitResult:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.repo_path,
            )
            return GitResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
                command=" ".join(cmd),
                return_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return GitResult(
                success=False,
                output="",
                error="Git command timed out",
                command=" ".join(cmd),
                return_code=-1,
            )
        except Exception as e:
            return GitResult(
                success=False,
                output="",
                error=str(e),
                command=" ".join(cmd),
                return_code=-1,
            )
