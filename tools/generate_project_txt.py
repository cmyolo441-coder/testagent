from __future__ import annotations

import argparse
import itertools
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ContextSpec:
    name: str
    aggregates: int
    entities_per_aggregate: int
    commands: int
    queries: int
    workflows: int
    events: int
    projections: int
    consumers: int
    api_routes: int
    unit_tests: int
    integration_tests: int


def _slugify(name: str) -> str:
    out = []
    prev_underscore = False
    for ch in name.strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_underscore = False
            continue
        if not prev_underscore:
            out.append("_")
            prev_underscore = True
    s = "".join(out).strip("_")
    return s or "context"


def _variants(prefix: str, n: int, suffix: str = ".py") -> list[str]:
    w = max(2, len(str(n)))
    return [f"{prefix}_{i:0{w}d}{suffix}" for i in range(1, n + 1)]


def _paths(base: str, parts: list[str]) -> list[str]:
    return [f"{base}{p}" for p in parts]


def _header(now: datetime) -> list[str]:
    iso = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return [
        "ULTRA-ADVANCED PYTHON REAL-WORLD MONOREPO STRUCTURE",
        "",
        "GOALS",
        "- DDD + Hexagonal architecture + CQRS + Event Sourcing (optional) + Outbox + Saga orchestration",
        "- Multi-deployable: API + Workers + Schedulers + CLI + Admin + Migrations",
        "- Strong contracts: versioned schemas for events/commands, compatibility testing, codegen",
        "- Observability: tracing/metrics/logging/audit, SLO/SLA/alerts, runbooks",
        "- Security: secrets handling, policy enforcement, zero-trust boundaries, supply-chain hardening",
        "",
        f"GENERATED_AT_UTC: {iso}",
        "",
        "STRUCTURE (PATH LISTING)",
        "",
    ]


def _root_skeleton() -> list[str]:
    return [
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODEOWNERS",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".python-version",
        ".env.example",
        ".pre-commit-config.yaml",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        ".github/workflows/security.yml",
        ".github/dependabot.yml",
        "docker/Dockerfile.api",
        "docker/Dockerfile.worker",
        "docker/Dockerfile.scheduler",
        "docker/Dockerfile.migrations",
        "docker/Dockerfile.admin",
        "docker/docker-compose.yml",
        "scripts/bootstrap.py",
        "scripts/verify.py",
        "scripts/db_migrate.py",
        "scripts/seed_data.py",
        "docs/architecture/decisions/adr-0001-record-architecture.md",
        "docs/architecture/decisions/adr-0002-contract-evolution.md",
        "docs/architecture/decisions/adr-0003-outbox-pattern.md",
        "docs/architecture/decisions/adr-0004-cqrs-read-models.md",
        "docs/architecture/decisions/adr-0005-saga-orchestration.md",
        "docs/architecture/c4/context.md",
        "docs/architecture/c4/container.md",
        "docs/architecture/c4/component.md",
        "docs/architecture/threat-model.md",
        "docs/api/openapi.yaml",
        "docs/api/postman_collection.json",
        "docs/runbooks/incident-response.md",
        "docs/runbooks/deployments.md",
        "docs/runbooks/database.md",
        "configs/app/base.toml",
        "configs/app/dev.toml",
        "configs/app/stage.toml",
        "configs/app/prod.toml",
        "configs/logging/json.toml",
        "configs/logging/pretty.toml",
        "configs/policies/rate_limits.toml",
        "configs/policies/feature_flags.toml",
        "configs/policies/data_retention.toml",
        "configs/policies/pii_policy.toml",
        "infra/k8s/base/namespace.yaml",
        "infra/k8s/base/configmap.yaml",
        "infra/k8s/base/deployment-api.yaml",
        "infra/k8s/base/deployment-worker.yaml",
        "infra/k8s/base/service-api.yaml",
        "infra/k8s/base/ingress.yaml",
        "infra/k8s/overlays/dev/kustomization.yaml",
        "infra/k8s/overlays/stage/kustomization.yaml",
        "infra/k8s/overlays/prod/kustomization.yaml",
        "infra/terraform/modules/network/main.tf",
        "infra/terraform/modules/db/main.tf",
        "infra/terraform/modules/cache/main.tf",
        "infra/terraform/modules/queue/main.tf",
        "infra/terraform/modules/observability/main.tf",
        "infra/terraform/envs/dev/main.tf",
        "infra/terraform/envs/stage/main.tf",
        "infra/terraform/envs/prod/main.tf",
        "src/ultra_platform/__init__.py",
        "src/ultra_platform/__main__.py",
        "src/ultra_platform/bootstrap/__init__.py",
        "src/ultra_platform/bootstrap/composition_root.py",
        "src/ultra_platform/bootstrap/wiring.py",
        "src/ultra_platform/bootstrap/lifecycle.py",
        "src/ultra_platform/bootstrap/health.py",
        "src/ultra_platform/common/__init__.py",
        "src/ultra_platform/common/types/__init__.py",
        "src/ultra_platform/common/types/ids.py",
        "src/ultra_platform/common/types/money.py",
        "src/ultra_platform/common/types/time.py",
        "src/ultra_platform/common/errors/__init__.py",
        "src/ultra_platform/common/errors/domain.py",
        "src/ultra_platform/common/errors/application.py",
        "src/ultra_platform/common/errors/infrastructure.py",
        "src/ultra_platform/common/crypto/__init__.py",
        "src/ultra_platform/common/crypto/hashing.py",
        "src/ultra_platform/common/crypto/signing.py",
        "src/ultra_platform/common/serialization/__init__.py",
        "src/ultra_platform/common/serialization/json.py",
        "src/ultra_platform/common/serialization/msgpack.py",
        "src/ultra_platform/common/concurrency/__init__.py",
        "src/ultra_platform/common/concurrency/locks.py",
        "src/ultra_platform/common/concurrency/rate_limit.py",
        "src/ultra_platform/common/observability/__init__.py",
        "src/ultra_platform/common/observability/logging.py",
        "src/ultra_platform/common/observability/metrics.py",
        "src/ultra_platform/common/observability/tracing.py",
        "src/ultra_platform/common/observability/audit.py",
        "src/ultra_platform/common/config/__init__.py",
        "src/ultra_platform/common/config/loader.py",
        "src/ultra_platform/common/config/schema.py",
        "src/ultra_platform/common/config/secrets.py",
        "src/ultra_platform/common/utils/__init__.py",
        "src/ultra_platform/common/utils/typing.py",
        "src/ultra_platform/common/utils/retries.py",
        "src/ultra_platform/common/utils/clock.py",
        "src/ultra_platform/contracts/__init__.py",
        "src/ultra_platform/contracts/events/__init__.py",
        "src/ultra_platform/contracts/events/registry.py",
        "src/ultra_platform/contracts/commands/__init__.py",
        "src/ultra_platform/contracts/commands/registry.py",
        "src/ultra_platform/plugins/__init__.py",
        "src/ultra_platform/plugins/registry.py",
        "src/ultra_platform/plugins/samples/__init__.py",
        "src/ultra_platform/plugins/samples/sample_plugin.py",
        "src/ultra_platform/interfaces/__init__.py",
        "src/ultra_platform/interfaces/api/__init__.py",
        "src/ultra_platform/interfaces/api/asgi.py",
        "src/ultra_platform/interfaces/api/deps.py",
        "src/ultra_platform/interfaces/api/middleware/__init__.py",
        "src/ultra_platform/interfaces/api/middleware/request_id.py",
        "src/ultra_platform/interfaces/api/middleware/auth.py",
        "src/ultra_platform/interfaces/api/middleware/rate_limit.py",
        "src/ultra_platform/interfaces/api/routes/__init__.py",
        "src/ultra_platform/interfaces/api/routes/health.py",
        "src/ultra_platform/interfaces/workers/__init__.py",
        "src/ultra_platform/interfaces/workers/runner.py",
        "src/ultra_platform/interfaces/workers/tasks/__init__.py",
        "src/ultra_platform/interfaces/workers/tasks/process_outbox.py",
        "src/ultra_platform/interfaces/cli/__init__.py",
        "src/ultra_platform/interfaces/cli/main.py",
        "src/ultra_platform/interfaces/cli/commands/__init__.py",
        "src/ultra_platform/interfaces/cli/commands/run_api.py",
        "src/ultra_platform/interfaces/cli/commands/run_worker.py",
        "src/ultra_platform/interfaces/cli/commands/migrate.py",
        "src/ultra_platform/tools/__init__.py",
        "src/ultra_platform/tools/codegen/__init__.py",
        "src/ultra_platform/tools/codegen/openapi_codegen.py",
        "src/ultra_platform/tools/codegen/event_schema_codegen.py",
        "src/ultra_platform/tools/lint/__init__.py",
        "src/ultra_platform/tools/lint/rules.py",
        "src/ultra_platform/tools/release/__init__.py",
        "src/ultra_platform/tools/release/versioning.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
        "tests/e2e/__init__.py",
        "benchmarks/__init__.py",
    ]


def _contract_versions(name: str, max_version: int) -> list[str]:
    versions = []
    for v in range(1, max_version + 1):
        versions.extend(
            [
                f"src/ultra_platform/contracts/{name}/v{v}/__init__.py",
                f"src/ultra_platform/contracts/{name}/v{v}/schemas.py",
                f"src/ultra_platform/contracts/{name}/v{v}/codecs.py",
                f"src/ultra_platform/contracts/{name}/v{v}/compat.py",
            ]
        )
    return versions


def _context_paths(spec: ContextSpec) -> list[str]:
    ctx = _slugify(spec.name)
    base = f"src/ultra_platform/bounded_contexts/{ctx}/"

    domain_base = f"{base}domain/"
    application_base = f"{base}application/"
    infra_base = f"{base}infrastructure/"
    interfaces_base = f"{base}interfaces/"
    tests_base = f"tests/bounded_contexts/{ctx}/"

    lines = [
        f"{base}__init__.py",
        f"{domain_base}__init__.py",
        f"{domain_base}shared/__init__.py",
        f"{domain_base}shared/entities.py",
        f"{domain_base}shared/value_objects.py",
        f"{domain_base}shared/domain_events.py",
        f"{domain_base}shared/invariants.py",
        f"{domain_base}shared/specifications.py",
        f"{domain_base}shared/policies.py",
        f"{domain_base}shared/services.py",
        f"{domain_base}shared/snapshots.py",
        f"{domain_base}shared/metadata.py",
        f"{domain_base}shared/clock.py",
        f"{domain_base}shared/crypto.py",
        f"{domain_base}shared/rules.py",
        f"{domain_base}shared/ports.py",
        f"{domain_base}shared/replay.py",
        f"{application_base}__init__.py",
        f"{application_base}ports/__init__.py",
        f"{application_base}ports/repositories.py",
        f"{application_base}ports/unit_of_work.py",
        f"{application_base}ports/event_bus.py",
        f"{application_base}ports/outbox.py",
        f"{application_base}ports/clock.py",
        f"{application_base}ports/id_generator.py",
        f"{application_base}services/__init__.py",
        f"{application_base}services/idempotency.py",
        f"{application_base}services/permissions.py",
        f"{application_base}services/feature_flags.py",
        f"{application_base}services/validation.py",
        f"{application_base}services/policy_enforcement.py",
        f"{application_base}sagas/__init__.py",
        f"{application_base}sagas/orchestrator.py",
        f"{application_base}sagas/policies.py",
        f"{application_base}workflows/__init__.py",
        f"{application_base}workflows/engine.py",
        f"{application_base}workflows/retries.py",
        f"{application_base}workflows/timeouts.py",
        f"{application_base}read_models/__init__.py",
        f"{application_base}read_models/materializers.py",
        f"{application_base}read_models/consistency.py",
        f"{infra_base}__init__.py",
        f"{infra_base}db/__init__.py",
        f"{infra_base}db/session.py",
        f"{infra_base}db/unit_of_work.py",
        f"{infra_base}db/migrations/README.md",
        f"{infra_base}db/outbox/__init__.py",
        f"{infra_base}db/outbox/models.py",
        f"{infra_base}db/outbox/publisher.py",
        f"{infra_base}db/outbox/cleanup.py",
        f"{infra_base}messaging/__init__.py",
        f"{infra_base}messaging/event_bus.py",
        f"{infra_base}messaging/dead_letter/__init__.py",
        f"{infra_base}messaging/dead_letter/policies.py",
        f"{infra_base}cache/__init__.py",
        f"{infra_base}cache/client.py",
        f"{infra_base}cache/strategies.py",
        f"{infra_base}auth/__init__.py",
        f"{infra_base}auth/jwt.py",
        f"{infra_base}auth/api_keys.py",
        f"{infra_base}http/__init__.py",
        f"{infra_base}http/client.py",
        f"{infra_base}http/retries.py",
        f"{infra_base}filesystem/__init__.py",
        f"{infra_base}filesystem/storage.py",
        f"{infra_base}feature_flags/__init__.py",
        f"{infra_base}feature_flags/flags.py",
        f"{interfaces_base}__init__.py",
        f"{interfaces_base}api/__init__.py",
        f"{interfaces_base}api/routes/__init__.py",
        f"{interfaces_base}api/routes/_errors.py",
        f"{interfaces_base}workers/__init__.py",
        f"{interfaces_base}workers/runner.py",
        f"{interfaces_base}workers/tasks/__init__.py",
        f"{interfaces_base}cli/__init__.py",
        f"{interfaces_base}cli/main.py",
        f"{interfaces_base}cli/commands/__init__.py",
        f"{tests_base}__init__.py",
        f"{tests_base}unit/__init__.py",
        f"{tests_base}integration/__init__.py",
        f"{tests_base}contract/__init__.py",
        f"{tests_base}e2e/__init__.py",
    ]

    aggregate_files = []
    for a in range(1, spec.aggregates + 1):
        agg = f"aggregate_{a:02d}"
        aggregate_files.extend(
            [
                f"{domain_base}aggregates/__init__.py",
                f"{domain_base}aggregates/{agg}/__init__.py",
                f"{domain_base}aggregates/{agg}/root.py",
                f"{domain_base}aggregates/{agg}/commands.py",
                f"{domain_base}aggregates/{agg}/events.py",
                f"{domain_base}aggregates/{agg}/state.py",
                f"{domain_base}aggregates/{agg}/invariants.py",
                f"{domain_base}aggregates/{agg}/snapshots.py",
            ]
        )
        aggregate_files.extend(
            _paths(
                f"{domain_base}aggregates/{agg}/entities/",
                ["__init__.py"] + _variants("entity", spec.entities_per_aggregate),
            )
        )
        aggregate_files.extend(
            _paths(
                f"{domain_base}aggregates/{agg}/value_objects/",
                ["__init__.py"] + _variants("vo", max(3, spec.entities_per_aggregate)),
            )
        )
        aggregate_files.extend(
            _paths(
                f"{domain_base}aggregates/{agg}/policies/",
                ["__init__.py"] + _variants("policy", 4),
            )
        )
        aggregate_files.extend(
            _paths(
                f"{domain_base}aggregates/{agg}/specifications/",
                ["__init__.py"] + _variants("spec", 5),
            )
        )

    cmd_files = _paths(
        f"{application_base}commands/handlers/",
        ["__init__.py"] + _variants("handle_command", spec.commands),
    )
    cmd_files += _paths(
        f"{application_base}commands/dtos/",
        ["__init__.py"] + _variants("dto", max(3, spec.commands)),
    )
    cmd_files += _paths(
        f"{application_base}commands/validators/",
        ["__init__.py"] + _variants("validate", max(3, spec.commands)),
    )
    cmd_files += [
        f"{application_base}commands/__init__.py",
        f"{application_base}commands/router.py",
        f"{application_base}commands/middleware.py",
    ]

    qry_files = _paths(
        f"{application_base}queries/handlers/",
        ["__init__.py"] + _variants("handle_query", spec.queries),
    )
    qry_files += _paths(
        f"{application_base}queries/projections/",
        ["__init__.py"] + _variants("projection", spec.projections),
    )
    qry_files += [
        f"{application_base}queries/__init__.py",
        f"{application_base}queries/router.py",
        f"{application_base}queries/cache.py",
    ]

    evt_files = _paths(
        f"{infra_base}messaging/consumers/",
        ["__init__.py"] + _variants("consume", spec.consumers),
    )
    evt_files += _paths(
        f"{infra_base}messaging/producers/",
        ["__init__.py"] + _variants("publish", max(3, spec.events)),
    )
    evt_files += _paths(
        f"{infra_base}messaging/schemas/",
        ["__init__.py"] + _variants("event", spec.events),
    )

    repo_files = _paths(
        f"{infra_base}db/repositories/",
        ["__init__.py"] + _variants("repo", max(6, spec.aggregates)),
    )

    api_route_files = _paths(
        f"{interfaces_base}api/routes/",
        _variants("route", spec.api_routes),
    )
    api_route_files += [
        f"{interfaces_base}api/asgi.py",
        f"{interfaces_base}api/deps.py",
        f"{interfaces_base}api/middleware/__init__.py",
        f"{interfaces_base}api/middleware/request_id.py",
        f"{interfaces_base}api/middleware/auth.py",
        f"{interfaces_base}api/middleware/rate_limit.py",
        f"{interfaces_base}api/middleware/observability.py",
    ]

    worker_task_files = _paths(
        f"{interfaces_base}workers/tasks/",
        ["__init__.py"] + _variants("task", max(8, spec.workflows)),
    )

    test_files = _paths(
        f"{tests_base}unit/",
        ["__init__.py"] + _variants("test_unit", spec.unit_tests),
    )
    test_files += _paths(
        f"{tests_base}integration/",
        ["__init__.py"] + _variants("test_integration", spec.integration_tests),
    )
    test_files += _paths(
        f"{tests_base}contract/",
        ["__init__.py"] + _variants("test_contract", max(5, spec.events)),
    )
    test_files += _paths(
        f"{tests_base}e2e/",
        ["__init__.py"] + _variants("test_e2e", max(4, spec.api_routes)),
    )

    return lines + aggregate_files + cmd_files + qry_files + evt_files + repo_files + api_route_files + worker_task_files + test_files


def _service_matrix(min_services: int) -> list[str]:
    names = [
        "api_gateway",
        "auth_service",
        "billing_service",
        "workflow_service",
        "notification_service",
        "search_service",
        "analytics_service",
        "admin_service",
        "scheduler_service",
        "audit_service",
        "fraud_service",
        "ml_service",
    ]
    while len(names) < min_services:
        names.append(f"service_{len(names) + 1:03d}")

    base = "src/services/"
    out = []
    for svc in names:
        svc_base = f"{base}{svc}/"
        out.extend(
            [
                f"{svc_base}__init__.py",
                f"{svc_base}bootstrap.py",
                f"{svc_base}settings.py",
                f"{svc_base}entrypoints/__init__.py",
                f"{svc_base}entrypoints/api.py",
                f"{svc_base}entrypoints/worker.py",
                f"{svc_base}entrypoints/scheduler.py",
                f"{svc_base}entrypoints/cli.py",
                f"{svc_base}observability/__init__.py",
                f"{svc_base}observability/logging.py",
                f"{svc_base}observability/metrics.py",
                f"{svc_base}observability/tracing.py",
                f"{svc_base}security/__init__.py",
                f"{svc_base}security/policy.py",
                f"{svc_base}security/secrets.py",
                f"{svc_base}adapters/__init__.py",
                f"{svc_base}adapters/db.py",
                f"{svc_base}adapters/messaging.py",
                f"{svc_base}adapters/cache.py",
                f"{svc_base}adapters/http_clients.py",
                f"{svc_base}application/__init__.py",
                f"{svc_base}application/commands.py",
                f"{svc_base}application/queries.py",
                f"{svc_base}application/workflows.py",
                f"{svc_base}domain/__init__.py",
                f"{svc_base}domain/model.py",
                f"{svc_base}domain/events.py",
                f"{svc_base}domain/rules.py",
                f"{svc_base}domain/policies.py",
                f"{svc_base}contracts/__init__.py",
                f"{svc_base}contracts/events_v1.py",
                f"{svc_base}contracts/commands_v1.py",
                f"{svc_base}tests/__init__.py",
                f"{svc_base}tests/test_smoke.py",
            ]
        )
        out.extend(_paths(f"{svc_base}application/handlers/", ["__init__.py"] + _variants("handler", 20)))
        out.extend(_paths(f"{svc_base}domain/aggregates/", ["__init__.py"] + _variants("aggregate", 12)))
        out.extend(_paths(f"{svc_base}entrypoints/routes/", ["__init__.py"] + _variants("route", 25)))
    return out


def _extra_real_world_layers(scale: int) -> list[str]:
    base = "src/ultra_platform/enterprise/"
    out = [
        f"{base}__init__.py",
        f"{base}governance/__init__.py",
        f"{base}governance/arch_rules.py",
        f"{base}governance/review_gates.py",
        f"{base}governance/compatibility.py",
        f"{base}security/__init__.py",
        f"{base}security/permissions.py",
        f"{base}security/policy_engine.py",
        f"{base}security/abac.py",
        f"{base}security/rbac.py",
        f"{base}security/crypto_boundary.py",
        f"{base}platform/__init__.py",
        f"{base}platform/feature_flags.py",
        f"{base}platform/rate_limits.py",
        f"{base}platform/idempotency.py",
        f"{base}platform/tenancy.py",
        f"{base}platform/sharding.py",
        f"{base}platform/consistency.py",
        f"{base}platform/backpressure.py",
        f"{base}platform/job_queue.py",
        f"{base}platform/scheduling.py",
        f"{base}platform/rollouts.py",
        f"{base}platform/observability.py",
        f"{base}data/__init__.py",
        f"{base}data/schema_registry.py",
        f"{base}data/contract_tests.py",
        f"{base}data/read_models.py",
        f"{base}data/event_store.py",
        f"{base}data/snapshots.py",
        f"{base}data/migrations.py",
        f"{base}data/outbox.py",
        f"{base}data/retention.py",
        f"{base}data/pii_redaction.py",
    ]

    out.extend(_paths(f"{base}governance/linters/", ["__init__.py"] + _variants("rule", max(50, scale))))
    out.extend(_paths(f"{base}security/policies/", ["__init__.py"] + _variants("policy", max(80, scale))))
    out.extend(_paths(f"{base}platform/capabilities/", ["__init__.py"] + _variants("capability", max(120, scale))))
    out.extend(_paths(f"{base}data/pipelines/", ["__init__.py"] + _variants("pipeline", max(120, scale))))
    out.extend(_paths("docs/runbooks/", _variants("runbook", max(120, scale), suffix=".md")))
    out.extend(_paths("docs/architecture/decisions/", _variants("adr", max(300, scale), suffix=".md")))
    return out


def _make_specs(seed: int, contexts: int) -> list[ContextSpec]:
    r = random.Random(seed)

    realistic_names = [
        "Identity",
        "Access Control",
        "Billing",
        "Invoicing",
        "Payments",
        "Subscriptions",
        "Catalog",
        "Orders",
        "Shipping",
        "Inventory",
        "Pricing",
        "Promotions",
        "Notifications",
        "Search",
        "Recommendations",
        "Analytics",
        "Audit",
        "Fraud",
        "Workflow",
        "Support",
    ]

    remaining = max(0, contexts - len(realistic_names))
    generated = [f"Domain Area {i:03d}" for i in range(1, remaining + 1)]
    names = realistic_names + generated

    specs: list[ContextSpec] = []
    for name in names:
        aggregates = r.randint(7, 14)
        entities_per_aggregate = r.randint(6, 12)
        commands = r.randint(22, 38)
        queries = r.randint(20, 34)
        workflows = r.randint(10, 18)
        events = r.randint(18, 34)
        projections = r.randint(10, 18)
        consumers = r.randint(12, 24)
        api_routes = r.randint(18, 30)
        unit_tests = r.randint(30, 60)
        integration_tests = r.randint(18, 40)
        specs.append(
            ContextSpec(
                name=name,
                aggregates=aggregates,
                entities_per_aggregate=entities_per_aggregate,
                commands=commands,
                queries=queries,
                workflows=workflows,
                events=events,
                projections=projections,
                consumers=consumers,
                api_routes=api_routes,
                unit_tests=unit_tests,
                integration_tests=integration_tests,
            )
        )
    return specs


def generate(min_lines: int, seed: int) -> list[str]:
    now = datetime.now(tz=timezone.utc)
    specs = _make_specs(seed=seed, contexts=80)

    lines: list[str] = []
    lines.extend(_header(now))
    lines.extend(_root_skeleton())
    lines.extend(_contract_versions("events", 8))
    lines.extend(_contract_versions("commands", 8))

    lines.append("")
    lines.append("BOUNDED CONTEXTS")
    lines.append("")

    for spec in specs:
        ctx = _slugify(spec.name)
        lines.append(f"[{ctx}]")
        lines.extend(_context_paths(spec))
        lines.append("")

    lines.append("MICROSERVICES (OPTIONAL DEPLOYABLES)")
    lines.append("")
    lines.extend(_service_matrix(min_services=40))

    lines.append("")
    lines.append("ENTERPRISE PLATFORM LAYERS")
    lines.append("")
    lines.extend(_extra_real_world_layers(scale=500))

    lines.append("")
    lines.append("NOTES")
    lines.append("- Yeh listing 'paths' form me hai (real repos me yahi sab files hote hain).")
    lines.append("- Aap chaho to isse actual folders/files create karwa sakte ho, ya sirf blueprint ke liye use karo.")
    lines.append("- Framework code hamesha interfaces/ (delivery) me rakho, domain/ ko pure rakho.")
    lines.append("- Contracts versioning v1..vN se distributed systems me safe evolution hota hai.")
    lines.append("- Outbox + consumers se exactly-once-ish processing practical hoti hai.")

    if len(lines) >= min_lines:
        return lines

    pad_base = "src/ultra_platform/_generated/"
    lines.append("")
    lines.append("AUTO-GENERATED PADDING (FOR LARGE REAL-WORLD BLUEPRINT SCALE)")
    lines.append("")

    extra = min_lines - len(lines)
    block = [
        f"{pad_base}__init__.py",
        f"{pad_base}readme.md",
        f"{pad_base}catalog/__init__.py",
        f"{pad_base}catalog/indexes.py",
        f"{pad_base}catalog/materializers.py",
        f"{pad_base}pipelines/__init__.py",
        f"{pad_base}pipelines/etl.py",
        f"{pad_base}pipelines/streaming.py",
        f"{pad_base}pipelines/backfills.py",
        f"{pad_base}governance/__init__.py",
        f"{pad_base}governance/policies.py",
        f"{pad_base}governance/rules.py",
        f"{pad_base}governance/gates.py",
        f"{pad_base}observability/__init__.py",
        f"{pad_base}observability/logging.py",
        f"{pad_base}observability/metrics.py",
        f"{pad_base}observability/tracing.py",
        f"{pad_base}security/__init__.py",
        f"{pad_base}security/crypto.py",
        f"{pad_base}security/secrets.py",
        f"{pad_base}security/policy_engine.py",
    ]

    i = 0
    while extra > 0:
        for b in block:
            if extra <= 0:
                break
            lines.append(b.replace(".py", f"_{i:05d}.py") if b.endswith(".py") else f"{b}.{i:05d}")
            extra -= 1
            i += 1

    return lines


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(Path.cwd() / "project.txt"))
    p.add_argument("--min-lines", type=int, default=10050)
    p.add_argument("--seed", type=int, default=1337)
    args = p.parse_args()

    out_path = Path(args.output)
    lines = generate(min_lines=args.min_lines, seed=args.seed)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

