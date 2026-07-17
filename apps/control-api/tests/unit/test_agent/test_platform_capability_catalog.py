from agenttest.modules.test_agent.domain.entities import RiskLevel

EXPECTED_PLATFORM_GROUPS = {
    "agents.list": "assets",
    "agents.create": "assets",
    "agents.publish_version": "assets",
    "agents.create_version": "assets",
    "datasets.list": "assets",
    "datasets.create_with_cases": "assets",
    "datasets.publish_version": "assets",
    "datasets.auto_generate_cases": "assets",
    "test_cases.list": "assets",
    "test_cases.get": "assets",
    "test_cases.create": "assets",
    "test_cases.update": "assets",
    "test_cases.validate": "assets",
    "test_cases.mark_ready": "assets",
    "test_cases.trial_run": "assets",
    "test_plans.list": "assets",
    "test_plans.create_version": "assets",
    "test_plans.publish_version": "assets",
    "environments.list": "assets",
    "environments.create": "assets",
    "credentials.list": "assets",
    "credentials.validate": "assets",
    "credentials.create": "assets",
    "runs.list": "execution",
    "runs.get_status": "execution",
    "runs.start": "execution",
    "runs.cancel": "execution",
    "agents.analyze_endpoint": "execution",
    "reports.generate": "execution",
    "scorers.list": "quality",
    "scorers.create": "quality",
    "experiments.list": "quality",
    "experiments.create": "quality",
    "security_scans.list": "quality",
    "security_scans.start": "quality",
    "reviews.list": "quality",
    "reviews.enqueue": "quality",
    "release_gates.list": "quality",
    "release_gates.evaluate": "quality",
}


def test_catalog_covers_every_professional_console_module() -> None:
    from agenttest.modules.test_agent.application.platform_catalog import capability_specs

    specs = capability_specs()
    names = {spec.name for spec in specs}

    assert names >= {
        "agents.list",
        "agents.create",
        "environments.list",
        "datasets.create_with_cases",
        "test_cases.list",
        "test_cases.get",
        "test_cases.create",
        "test_cases.update",
        "test_cases.validate",
        "test_cases.mark_ready",
        "test_cases.trial_run",
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
    assert (
        next(spec for spec in specs if spec.name == "test_cases.trial_run").risk
        is RiskLevel.HIGH_IMPACT
    )
    assert next(spec for spec in specs if spec.name == "test_cases.validate").risk is RiskLevel.READ


def test_every_platform_capability_has_one_feature_group() -> None:
    from agenttest.modules.test_agent.adapters.platform import capability_group_for
    from agenttest.modules.test_agent.application.platform_catalog import capability_specs

    platform_names = {
        spec.name for spec in capability_specs() if not spec.name.startswith("test_missions.")
    }

    assert platform_names == set(EXPECTED_PLATFORM_GROUPS)
    assert {name: capability_group_for(name) for name in platform_names} == EXPECTED_PLATFORM_GROUPS
