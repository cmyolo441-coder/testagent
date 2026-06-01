"""Real Tests — Verify core functionality"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engines", "planning-engine", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engines", "safety-engine", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engines", "memory-engine", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engines", "truth-engine", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engines", "agent-engine", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "tool-executor", "src"))


def test_mission_contract():
    from planning_engine.mission_control.mission_contract import MissionContract
    contract = MissionContract(id="M-test", goal="Build software company")
    assert contract.id == "M-test"
    assert contract.goal == "Build software company"
    can_exec, reason = contract.can_execute()
    assert can_exec
    print("✓ MissionContract")


def test_objective_tree():
    from planning_engine.mission_control.objective_tree import ObjectiveTree
    tree = ObjectiveTree.from_goal("Build a software company in 6 months", "M-001")
    assert tree.root is not None
    assert len(tree.root.children) > 0
    progress = tree.calculate_progress()
    assert progress == 0.0
    print("✓ ObjectiveTree")


def test_milestone_planner():
    from planning_engine.mission_control.milestone_planner import MilestonePlanner
    from planning_engine.mission_control.objective_tree import ObjectiveTree
    tree = ObjectiveTree.from_goal("Build software company", "M-001")
    planner = MilestonePlanner("6m")
    milestones = planner.generate_milestones(tree)
    assert len(milestones) > 0
    assert all("Month" in m["title"] for m in milestones)
    print("✓ MilestonePlanner")


def test_risk_assessor():
    from safety_engine.risk.risk_model import RiskAssessor
    risk = RiskAssessor()
    score = risk.assess_command("rm -rf /")
    assert score >= 70
    score = risk.assess_command("ls -la")
    assert score < 30
    print("✓ RiskAssessor")


def test_approval_store():
    from safety_engine.approvals.approval_store import ApprovalStore
    store = ApprovalStore()
    req = store.request_approval("shell", "run dangerous command", 70)
    assert req.status.value == "pending"
    store.approve(req.id)
    assert req.status.value == "approved"
    print("✓ ApprovalStore")


def test_sqlite_memory():
    import tempfile
    from memory_engine.stores.sqlite_store import SQLiteMemoryStore, MemoryRecord
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        store = SQLiteMemoryStore(f.name)
        record = MemoryRecord(content="Test memory", importance=0.8)
        rid = store.store(record)
        retrieved = store.retrieve(rid)
        assert retrieved is not None
        assert retrieved.content == "Test memory"
        results = store.search("Test")
        assert len(results) > 0
        print("✓ SQLiteMemoryStore")


def test_working_memory():
    from memory_engine.working_memory import WorkingMemory
    wm = WorkingMemory(max_items=5)
    wm.add("user", "Hello")
    wm.add("assistant", "Hi there")
    context = wm.get_context()
    assert len(context) == 2
    wm.clear()
    assert len(wm.get_context()) == 0
    print("✓ WorkingMemory")


def test_claim_extractor():
    from truth_engine.claim_extractor import ClaimExtractor
    ext = ClaimExtractor()
    claims = ext.extract_claims("Python is a programming language. It has 10 million users.")
    assert len(claims) > 0
    print("✓ ClaimExtractor")


def test_verification_reporter():
    from truth_engine.verification_reporter import VerificationReporter, VerificationStatus
    reporter = VerificationReporter()
    report = reporter.create_report("C-001", "Python is fast")
    reporter.add_evidence(report.id, "source", "Benchmarks show high performance", "benchmark.org", 0.8)
    assert report.evidence_count == 1
    print("✓ VerificationReporter")


def test_agent_loop():
    from agent_engine.core.agent_loop import AgentLoop
    loop = AgentLoop(max_iterations=3)
    observations = ["Step 1", "Step 2", "Step 3"]
    idx = [0]

    def observe(ctx):
        i = idx[0]
        idx[0] += 1
        return observations[min(i, len(observations) - 1)]

    def think(ctx, obs):
        return f"Thinking about {obs}"

    def act(ctx, thought):
        return {"result": "done"}

    def stop(ctx, step):
        return step.iteration >= 2

    loop.set_observe(observe)
    loop.set_think(think)
    loop.set_act(act)
    loop.set_stop(stop)
    steps = loop.run()
    assert len(steps) > 0
    print("✓ AgentLoop")


def test_tool_registry():
    from tool_executor.runtime.tool_registry import ToolRegistry, ToolDefinition, ToolCategory
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="echo",
        description="Echo input",
        category=ToolCategory.CUSTOM,
        handler=lambda text="": text,
    )
    registry.register(tool)
    assert registry.get("echo") is not None
    tools = registry.list_tools()
    assert len(tools) == 1
    print("✓ ToolRegistry")


def test_working_memory_importance():
    from memory_engine.working_memory import WorkingMemory
    wm = WorkingMemory(max_items=3)
    for i in range(5):
        wm.add("user", f"Message {i}")
    assert len(wm.items) == 3
    print("✓ WorkingMemory eviction")


def test_progress_tracker():
    from planning_engine.mission_control.progress_tracker import ProgressTracker
    tracker = ProgressTracker()
    tasks = [
        {"status": "done", "risk_level": "low"},
        {"status": "done", "risk_level": "medium"},
        {"status": "pending", "risk_level": "high"},
    ]
    report = tracker.calculate_progress(tasks, "M-001")
    assert report.progress_percent > 0
    print("✓ ProgressTracker")


def test_dependency_graph():
    from planning_engine.mission_control.dependency_graph import DependencyGraph, Dependency
    graph = DependencyGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_dependency(Dependency("A", "B"))
    order = graph.topological_sort()
    assert order.index("A") < order.index("B")
    print("✓ DependencyGraph")


if __name__ == "__main__":
    tests = [
        test_mission_contract,
        test_objective_tree,
        test_milestone_planner,
        test_risk_assessor,
        test_approval_store,
        test_sqlite_memory,
        test_working_memory,
        test_claim_extractor,
        test_verification_reporter,
        test_agent_loop,
        test_tool_registry,
        test_working_memory_importance,
        test_progress_tracker,
        test_dependency_graph,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed > 0:
        sys.exit(1)
