"""Explicit registration of every Control API SQLAlchemy model."""

from sqlalchemy import MetaData

from agenttest.modules.agents.infrastructure.persistence import models as _agents
from agenttest.modules.audit.infrastructure.persistence import models as _audit
from agenttest.modules.browser_profiles.infrastructure import models as _browser_profiles
from agenttest.modules.datasets.infrastructure.persistence import models as _datasets
from agenttest.modules.environments.infrastructure.persistence import models as _environments
from agenttest.modules.experiments.infrastructure.persistence import models as _experiments
from agenttest.modules.feedback.infrastructure.persistence import models as _feedback
from agenttest.modules.gates.infrastructure.persistence import models as _gates
from agenttest.modules.identity.infrastructure.persistence import models as _identity
from agenttest.modules.model_configs.infrastructure.persistence import models as _model_configs
from agenttest.modules.projects.infrastructure.persistence import models as _projects
from agenttest.modules.reviews.infrastructure.persistence import models as _reviews
from agenttest.modules.run_postprocessing.infrastructure import models as _run_postprocessing
from agenttest.modules.runs.infrastructure.persistence import models as _runs
from agenttest.modules.scorers.infrastructure.persistence import models as _scorers
from agenttest.modules.security.infrastructure import models as _security
from agenttest.modules.test_accounts.infrastructure.persistence import models as _test_accounts
from agenttest.modules.test_agent.infrastructure import models as _test_agent
from agenttest.modules.test_missions.infrastructure import models as _test_missions
from agenttest.modules.test_plans.infrastructure.persistence import models as _test_plans
from agenttest.modules.user_settings.infrastructure.persistence import models as _user_settings
from agenttest.shared.infrastructure.database import Base

# The aliases make the registration imports intentional and visible to static analysis.
_REGISTERED_MODEL_MODULES = (
    _agents,
    _audit,
    _browser_profiles,
    _datasets,
    _environments,
    _experiments,
    _feedback,
    _gates,
    _identity,
    _model_configs,
    _projects,
    _reviews,
    _run_postprocessing,
    _runs,
    _scorers,
    _security,
    _test_accounts,
    _test_agent,
    _test_missions,
    _test_plans,
    _user_settings,
)


def register_models() -> MetaData:
    """Return complete metadata after importing every persistence model module."""
    return Base.metadata
