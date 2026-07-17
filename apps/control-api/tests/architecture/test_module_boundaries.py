import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import scripts.check_architecture as architecture
from scripts.check_architecture import find_violations, module_name_for


def write_module(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_current_control_api_respects_module_boundaries() -> None:
    source_root = Path("apps/control-api/src")

    assert find_violations(source_root) == []


def test_domain_cannot_import_frameworks(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/identity/domain/entities.py",
        "from sqlalchemy import String\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/identity/domain/entities.py: "
        "domain imports forbidden dependency sqlalchemy"
    ]


def test_domain_cannot_import_outward_layers(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/feedback/domain/entities.py",
        "from agenttest.modules.feedback.api.schemas import FeedbackType\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/feedback/domain/entities.py: domain imports outward layer "
        "agenttest.modules.feedback.api.schemas"
    ]


def test_application_cannot_import_outward_layers(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/feedback/application/commands.py",
        "from agenttest.modules.feedback.api.schemas import FeedbackType\n"
        "from agenttest.modules.feedback.infrastructure.persistence.repositories "
        "import SqlAlchemyFeedbackRepository\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/feedback/application/commands.py: application imports "
        "outward layer agenttest.modules.feedback.api.schemas",
        "agenttest/modules/feedback/application/commands.py: application imports "
        "outward layer agenttest.modules.feedback.infrastructure.persistence.repositories",
    ]


def test_relative_imports_cannot_bypass_layer_rules(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/feedback/domain/entities.py",
        "from ..api.schemas import FeedbackType\n",
    )
    write_module(
        tmp_path,
        "agenttest/modules/feedback/application/commands.py",
        "from ..infrastructure.persistence.repositories import FeedbackRepository\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/feedback/application/commands.py: application imports "
        "outward layer agenttest.modules.feedback.infrastructure.persistence.repositories",
        "agenttest/modules/feedback/domain/entities.py: domain imports outward layer "
        "agenttest.modules.feedback.api.schemas",
    ]


def test_application_cannot_import_frameworks(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/runs/application/commands.py",
        "from fastapi import HTTPException\nfrom sqlalchemy import select\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/runs/application/commands.py: application imports forbidden "
        "dependency fastapi",
        "agenttest/modules/runs/application/commands.py: application imports forbidden "
        "dependency sqlalchemy",
    ]


def test_execution_surfaces_cannot_import_control_plane_or_database_drivers(
    tmp_path: Path,
) -> None:
    write_module(
        tmp_path,
        "workers/api_runner/task.py",
        "from agenttest.modules.runs.public import Run\nfrom sqlalchemy import select\n",
    )

    violations = architecture.find_execution_surface_violations(tmp_path / "workers", "worker")

    assert violations == [
        "api_runner/task.py: worker imports control-plane module agenttest.modules.runs.public",
        "api_runner/task.py: worker imports business database dependency sqlalchemy",
    ]

    write_module(
        tmp_path,
        "plugins/canvas_agent/adapter.py",
        "from agenttest.modules.runs.public import Run\nfrom asyncpg import Connection\n",
    )

    plugin_violations = architecture.find_execution_surface_violations(
        tmp_path / "plugins", "plugin"
    )

    assert plugin_violations == [
        "canvas_agent/adapter.py: plugin imports control-plane module "
        "agenttest.modules.runs.public",
        "canvas_agent/adapter.py: plugin imports business database dependency asyncpg",
    ]


def test_api_cannot_import_infrastructure_models(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/identity/api/router.py",
        "from agenttest.modules.identity.infrastructure.persistence.models import UserModel\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/identity/api/router.py: API imports infrastructure persistence models"
    ]


def test_api_cannot_import_infrastructure_or_sqlalchemy(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/runs/api/router.py",
        "from sqlalchemy import text\n",
    )

    assert find_violations(tmp_path) == [
        "agenttest/modules/runs/api/router.py: API imports forbidden dependency sqlalchemy"
    ]


def test_api_cannot_import_module_infrastructure(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/runs/api/router.py",
        "from agenttest.modules.runs.infrastructure.persistence.repositories import Repo\n",
    )

    assert find_violations(tmp_path) == [
        "agenttest/modules/runs/api/router.py: API imports module infrastructure"
    ]


def test_api_cannot_call_session_execute_or_scalar(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/runs/api/router.py",
        "async def f(session):\n    await session.execute('x')\n    await session.scalar('y')\n",
    )

    assert find_violations(tmp_path) == [
        "agenttest/modules/runs/api/router.py: API performs persistence call session.execute",
        "agenttest/modules/runs/api/router.py: API performs persistence call session.scalar",
    ]


def test_cross_module_imports_must_use_public_module(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "agenttest/modules/projects/application/queries.py",
        "from agenttest.modules.identity.domain.entities import User\n",
    )

    violations = find_violations(tmp_path)

    assert violations == [
        "agenttest/modules/projects/application/queries.py: cross-module import must use "
        "agenttest.modules.identity.public"
    ]


def test_bootstrap_modules_directory_is_not_a_domain_module() -> None:
    assert module_name_for(Path("agenttest/bootstrap/modules/core.py")) is None
