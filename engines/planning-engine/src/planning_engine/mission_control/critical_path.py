"""Critical Path Method — Calculate project timeline and critical tasks"""
from dataclasses import dataclass
from planning_engine.mission_control.dependency_graph import DependencyGraph


@dataclass
class TaskEstimate:
    task_id: str
    optimistic: int   # days
    pessimistic: int  # days
    most_likely: int  # days

    @property
    def expected(self) -> float:
        """PERT expected duration."""
        return (self.optimistic + 4 * self.most_likely + self.pessimistic) / 6

    @property
    def variance(self) -> float:
        """PERT variance."""
        return ((self.pessimistic - self.optimistic) / 6) ** 2


class CriticalPathAnalyzer:
    """Analyze critical path and project timeline."""

    def __init__(self, graph: DependencyGraph, estimates: dict[str, TaskEstimate]):
        self.graph = graph
        self.estimates = estimates

    def calculate_earliest_times(self) -> tuple[dict[str, float], dict[str, float]]:
        topo = self.graph.topological_sort()
        es = {n: 0.0 for n in self.graph.nodes}
        ef = {n: 0.0 for n in self.graph.nodes}

        for node in topo:
            est = self.estimates.get(node)
            duration = est.expected if est else 1.0
            ef[node] = es[node] + duration
            for dep in self.graph.edges.get(node, []):
                if ef[node] > es[dep.target_id]:
                    es[dep.target_id] = ef[node]

        return es, ef

    def calculate_latest_times(self, project_end: float) -> tuple[dict[str, float], dict[str, float]]:
        topo = list(reversed(self.graph.topological_sort()))
        lf = {n: project_end for n in self.graph.nodes}
        ls = {n: project_end for n in self.graph.nodes}

        for node in topo:
            est = self.estimates.get(node)
            duration = est.expected if est else 1.0
            ls[node] = lf[node] - duration
            for dep in self.graph.edges.get(node, []):
                if ls[node] < lf[dep.source_id]:
                    lf[dep.source_id] = ls[node]

        return ls, lf

    def analyze(self) -> dict:
        es, ef = self.calculate_earliest_times()
        project_end = max(ef.values()) if ef else 0
        ls, lf = self.calculate_latest_times(project_end)

        slack = {}
        critical_path = []
        for node in self.graph.nodes:
            slack[node] = ls[node] - es[node]
            if abs(slack[node]) < 0.001:
                critical_path.append(node)

        total_variance = sum(
            self.estimates[n].variance for n in critical_path if n in self.estimates
        )
        std_dev = total_variance ** 0.5

        return {
            "project_duration_days": project_end,
            "critical_path": critical_path,
            "critical_path_length": len(critical_path),
            "total_variance": total_variance,
            "std_deviation": std_dev,
            "slack": slack,
            "task_details": {
                n: {
                    "es": es[n], "ef": ef[n],
                    "ls": ls[n], "lf": lf[n],
                    "slack": slack[n],
                    "is_critical": abs(slack[n]) < 0.001,
                }
                for n in self.graph.nodes
            },
        }
