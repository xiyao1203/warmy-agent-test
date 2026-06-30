from agenttest.modules.test_agent.domain.entities import RiskLevel


def test_catalog_covers_every_professional_console_module() -> None:
    from agenttest.modules.test_agent.application.platform_catalog import capability_specs

    specs = capability_specs()
    names = {spec.name for spec in specs}

    assert names >= {
        "agents.list",
        "agents.create",
        "environments.list",
        "datasets.create_with_cases",
        "test_plans.create_version",
        "runs.start",
        "scorers.list",
        "experiments.create",
        "security_scans.start",
        "reviews.enqueue",
        "release_gates.evaluate",
    }
    assert next(spec for spec in specs if spec.name == "runs.start").risk is RiskLevel.HIGH_IMPACT
    assert next(spec for spec in specs if spec.name == "agents.list").risk is RiskLevel.READ
