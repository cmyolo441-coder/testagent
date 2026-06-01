"""Monitoring Tools — Metrics, alerts, and health checks"""
import subprocess
import json
import time
import os
import platform
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class MonitoringResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    operation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "operation": self.operation,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }


@dataclass
class Alert:
    name: str
    severity: str  # info, warning, critical
    message: str
    metric_name: str
    metric_value: float
    threshold: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "severity": self.severity,
            "message": self.message,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
        }


class MonitoringTools:
    """Metrics, alerts, and health checks."""

    ALERT_RULES = {
        "cpu_high": {"metric": "cpu_percent", "threshold": 90, "severity": "warning"},
        "memory_high": {"metric": "memory_percent", "threshold": 85, "severity": "warning"},
        "memory_critical": {"metric": "memory_percent", "threshold": 95, "severity": "critical"},
        "disk_high": {"metric": "disk_percent", "threshold": 90, "severity": "warning"},
        "disk_critical": {"metric": "disk_percent", "threshold": 95, "severity": "critical"},
        "load_high": {"metric": "load_1m", "threshold": 8, "severity": "warning"},
    }

    def __init__(self):
        self._alerts: list[Alert] = []
        self._metrics_history: list[dict] = []

    def metrics(self) -> MonitoringResult:
        start = time.time()

        try:
            cpu_percent = self._get_cpu_percent()
            memory = self._get_memory_info()
            disk = self._get_disk_info()
            load = os.getloadavg()

            metrics_data = {
                "cpu_percent": cpu_percent,
                "cpu_count": os.cpu_count(),
                "memory_total_mb": memory["total_mb"],
                "memory_used_mb": memory["used_mb"],
                "memory_percent": memory["percent"],
                "disk_total_gb": disk["total_gb"],
                "disk_used_gb": disk["used_gb"],
                "disk_percent": disk["percent"],
                "load_1m": load[0],
                "load_5m": load[1],
                "load_15m": load[2],
                "uptime_seconds": self._get_uptime(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            }

            self._metrics_history.append({
                "timestamp": time.time(),
                "data": metrics_data,
            })

            self._check_alerts(metrics_data)

            duration = (time.time() - start) * 1000
            return MonitoringResult(
                success=True,
                data=metrics_data,
                operation="metrics",
                duration_ms=duration,
            )
        except Exception as e:
            return MonitoringResult(
                success=False,
                error=str(e),
                operation="metrics",
                duration_ms=(time.time() - start) * 1000,
            )

    def alerts(self, severity: str = None) -> MonitoringResult:
        start = time.time()
        alerts_data = [a.to_dict() for a in self._alerts]
        if severity:
            alerts_data = [a for a in alerts_data if a["severity"] == severity]

        return MonitoringResult(
            success=True,
            data={"alerts": alerts_data, "count": len(alerts_data)},
            operation="alerts",
            duration_ms=(time.time() - start) * 1000,
        )

    def health(self) -> MonitoringResult:
        start = time.time()

        checks = {
            "cpu": self._check_cpu_health(),
            "memory": self._check_memory_health(),
            "disk": self._check_disk_health(),
            "process": self._check_process_health(),
        }

        all_healthy = all(c["healthy"] for c in checks.values())

        duration = (time.time() - start) * 1000
        return MonitoringResult(
            success=True,
            data={
                "healthy": all_healthy,
                "checks": checks,
            },
            operation="health",
            duration_ms=duration,
        )

    def process_list(self, filter_name: str = "") -> MonitoringResult:
        start = time.time()
        try:
            result = subprocess.run(
                ["ps", "aux", "--sort=-pcpu"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            lines = result.stdout.strip().split("\n")
            processes = []
            for line in lines[1:]:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    proc = {
                        "user": parts[0],
                        "pid": int(parts[1]),
                        "cpu": float(parts[2]),
                        "mem": float(parts[3]),
                        "vsz": int(parts[4]),
                        "rss": int(parts[5]),
                        "command": parts[10],
                    }
                    if filter_name and filter_name.lower() not in proc["command"].lower():
                        continue
                    processes.append(proc)

            duration = (time.time() - start) * 1000
            return MonitoringResult(
                success=True,
                data={"processes": processes[:50], "total": len(processes)},
                operation="process_list",
                duration_ms=duration,
            )
        except Exception as e:
            return MonitoringResult(
                success=False,
                error=str(e),
                operation="process_list",
                duration_ms=(time.time() - start) * 1000,
            )

    def network_stats(self) -> MonitoringResult:
        start = time.time()
        try:
            result = subprocess.run(
                ["cat", "/proc/net/dev"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            interfaces = {}
            for line in result.stdout.strip().split("\n")[2:]:
                if ":" in line:
                    parts = line.split(":")
                    iface = parts[0].strip()
                    stats = parts[1].split()
                    if len(stats) >= 10:
                        interfaces[iface] = {
                            "rx_bytes": int(stats[0]),
                            "rx_packets": int(stats[1]),
                            "tx_bytes": int(stats[8]),
                            "tx_packets": int(stats[9]),
                        }

            duration = (time.time() - start) * 1000
            return MonitoringResult(
                success=True,
                data={"interfaces": interfaces},
                operation="network_stats",
                duration_ms=duration,
            )
        except Exception as e:
            return MonitoringResult(
                success=False,
                error=str(e),
                operation="network_stats",
                duration_ms=(time.time() - start) * 1000,
            )

    def disk_io(self) -> MonitoringResult:
        start = time.time()
        try:
            result = subprocess.run(
                ["iostat", "-d", "1", "1"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            duration = (time.time() - start) * 1000
            return MonitoringResult(
                success=True,
                data={"raw_output": result.stdout[:2000]},
                operation="disk_io",
                duration_ms=duration,
            )
        except FileNotFoundError:
            return MonitoringResult(
                success=True,
                data={"message": "iostat not available"},
                operation="disk_io",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return MonitoringResult(
                success=False,
                error=str(e),
                operation="disk_io",
                duration_ms=(time.time() - start) * 1000,
            )

    def clear_alerts(self):
        self._alerts.clear()

    def get_metrics_history(self, limit: int = 60) -> list[dict]:
        return self._metrics_history[-limit:]

    def _get_cpu_percent(self) -> float:
        try:
            result = subprocess.run(
                ["grep", "-c", "^processor", "/proc/cpuinfo"],
                capture_output=True, text=True, timeout=5,
            )
            cpu_count = int(result.stdout.strip()) or 1

            result = subprocess.run(
                ["cat", "/proc/stat"],
                capture_output=True, text=True, timeout=5,
            )
            line = result.stdout.split("\n")[0]
            values = line.split()[1:]
            total = sum(int(v) for v in values)
            idle = int(values[3])

            time.sleep(0.1)

            result = subprocess.run(
                ["cat", "/proc/stat"],
                capture_output=True, text=True, timeout=5,
            )
            line = result.stdout.split("\n")[0]
            values = line.split()[1:]
            total2 = sum(int(v) for v in values)
            idle2 = int(values[3])

            total_diff = total2 - total
            idle_diff = idle2 - idle

            if total_diff > 0:
                return round((1 - idle_diff / total_diff) * 100, 1)
            return 0.0
        except Exception:
            return 0.0

    def _get_memory_info(self) -> dict:
        try:
            with open("/proc/meminfo") as f:
                info = {}
                for line in f:
                    parts = line.split()
                    key = parts[0].rstrip(":")
                    info[key] = int(parts[1])

                total = info.get("MemTotal", 0) / 1024
                available = info.get("MemAvailable", info.get("MemFree", 0)) / 1024
                used = total - available
                percent = (used / total * 100) if total > 0 else 0

                return {
                    "total_mb": round(total),
                    "used_mb": round(used),
                    "available_mb": round(available),
                    "percent": round(percent, 1),
                }
        except Exception:
            return {"total_mb": 0, "used_mb": 0, "percent": 0}

    def _get_disk_info(self) -> dict:
        try:
            st = os.statvfs("/")
            total = st.f_blocks * st.f_frsize / (1024 ** 3)
            free = st.f_bavail * st.f_frsize / (1024 ** 3)
            used = total - free
            percent = (used / total * 100) if total > 0 else 0

            return {
                "total_gb": round(total, 2),
                "used_gb": round(used, 2),
                "free_gb": round(free, 2),
                "percent": round(percent, 1),
            }
        except Exception:
            return {"total_gb": 0, "used_gb": 0, "percent": 0}

    def _get_uptime(self) -> float:
        try:
            with open("/proc/uptime") as f:
                return float(f.read().split()[0])
        except Exception:
            return 0.0

    def _check_cpu_health(self) -> dict:
        cpu = self._get_cpu_percent()
        return {"healthy": cpu < 95, "value": cpu, "threshold": 95}

    def _check_memory_health(self) -> dict:
        mem = self._get_memory_info()
        return {"healthy": mem["percent"] < 95, "value": mem["percent"], "threshold": 95}

    def _check_disk_health(self) -> dict:
        disk = self._get_disk_info()
        return {"healthy": disk["percent"] < 95, "value": disk["percent"], "threshold": 95}

    def _check_process_health(self) -> dict:
        pid = os.getpid()
        return {"healthy": True, "pid": pid, "status": "running"}

    def _check_alerts(self, metrics: dict):
        for rule_name, rule in self.ALERT_RULES.items():
            value = metrics.get(rule["metric"], 0)
            if isinstance(value, (int, float)) and value >= rule["threshold"]:
                alert = Alert(
                    name=rule_name,
                    severity=rule["severity"],
                    message=f"{rule['metric']} is {value} (threshold: {rule['threshold']})",
                    metric_name=rule["metric"],
                    metric_value=value,
                    threshold=rule["threshold"],
                )
                self._alerts.append(alert)
