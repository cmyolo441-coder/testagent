"""Shell Tools — Safe shell command execution"""
import subprocess
import os
import shlex
from pathlib import Path
from typing import Optional
import signal
import sys


def execute_command(command: str, cwd: Optional[str] = None,
                   timeout: int = 30, env: Optional[dict] = None,
                   capture_output: bool = True) -> dict:
    """Execute a shell command safely."""
    try:
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=exec_env,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {
            "error": f"Command timed out after {timeout}s",
            "command": command,
            "success": False,
        }
    except Exception as e:
        return {
            "error": str(e),
            "command": command,
            "success": False,
        }


def run_python(code: str, timeout: int = 30) -> dict:
    """Execute Python code in a subprocess."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Python execution timed out after {timeout}s", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def run_python_file(script_path: str, args: Optional[list[str]] = None,
                   timeout: int = 60) -> dict:
    """Execute a Python script file."""
    p = Path(script_path)
    if not p.exists():
        return {"error": f"Script not found: {script_path}", "success": False}

    cmd = [sys.executable, str(p)] + (args or [])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "script": script_path,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Script timed out after {timeout}s", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def run_script(shell: str = "bash", command: str = "", timeout: int = 30) -> dict:
    """Execute a shell script."""
    shell_path = f"/bin/{shell}"
    if not Path(shell_path).exists():
        return {"error": f"Shell not found: {shell}", "success": False}

    try:
        result = subprocess.run(
            [shell_path, "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Script timed out after {timeout}s", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def get_system_info() -> dict:
    """Get system information."""
    import platform
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cwd": os.getcwd(),
        "user": os.getenv("USER", "unknown"),
        "pid": os.getpid(),
    }


def list_processes(filter_name: Optional[str] = None) -> dict:
    """List running processes."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = result.stdout.strip().split("\n")
        headers = lines[0].split()
        processes = []
        for line in lines[1:]:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                proc = {
                    "user": parts[0],
                    "pid": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "command": parts[10],
                }
                if filter_name and filter_name.lower() not in proc["command"].lower():
                    continue
                processes.append(proc)
        return {"processes": processes[:100], "total": len(processes)}
    except Exception as e:
        return {"error": str(e)}
