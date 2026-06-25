import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from scripts.check_architecture import find_violations


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
