"""画布 Agent 插件公开接口。"""

from agenttest_plugin_canvas.adapter import (
    CanvasAgentAdapter,
    CanvasArtifactAdapter,
    CanvasConnection,
    CanvasConnectionType,
    CanvasNode,
    CanvasNodeType,
    CanvasTrace,
)
from agenttest_plugin_canvas.scoring.multimodal import (
    HeuristicMultiModalScorer,
    MultiModalScorer,
    ScoreResult,
)
from agenttest_plugin_canvas.tapnow import TapNowBrowserContract

__all__ = [
    "CanvasAgentAdapter",
    "CanvasArtifactAdapter",
    "CanvasConnection",
    "CanvasConnectionType",
    "CanvasNode",
    "CanvasNodeType",
    "CanvasTrace",
    "TapNowBrowserContract",
    "HeuristicMultiModalScorer",
    "MultiModalScorer",
    "ScoreResult",
]
