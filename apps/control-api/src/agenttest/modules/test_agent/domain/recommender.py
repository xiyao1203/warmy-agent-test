"""智能推荐功能。

基于历史推荐测试集、环境模板和评分器。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Recommendation:
    """推荐结果。

    Attributes:
        id: 推荐项 ID。
        name: 推荐项名称。
        score: 推荐分数（0-1）。
        reason: 推荐原因。
    """

    id: str
    name: str
    score: float
    reason: str


class Recommender:
    """推荐器。

    功能：
    - 基于历史推荐测试集
    - 基于 Agent 类型推荐环境模板
    - 基于用例特征推荐评分器
    """

    def recommend_test_sets(
        self,
        agent_type: str,
        history: list[dict[str, object]],
        limit: int = 3,
    ) -> list[Recommendation]:
        """推荐测试集。

        Args:
            agent_type: Agent 类型。
            history: 历史测试记录。
            limit: 返回数量限制。

        Returns:
            推荐的测试集列表，按分数降序。
        """
        if not history:
            return []

        # 按成功率排序
        sorted_history = sorted(
            history,
            key=lambda x: float(x.get("success_rate", 0)),  # type: ignore[arg-type]
            reverse=True,
        )

        recommendations: list[Recommendation] = []
        for item in sorted_history[:limit]:
            test_set_id = str(item.get("test_set_id", ""))
            success_rate = float(item.get("success_rate", 0))
            recommendations.append(
                Recommendation(
                    id=test_set_id,
                    name=f"测试集 {test_set_id}",
                    score=success_rate,
                    reason=f"历史成功率 {success_rate:.0%}",
                )
            )

        return recommendations

    def recommend_environment_templates(
        self,
        agent_type: str,
        templates: list[dict[str, object]],
        limit: int = 3,
    ) -> list[Recommendation]:
        """推荐环境模板。

        Args:
            agent_type: Agent 类型。
            templates: 可用模板列表。
            limit: 返回数量限制。

        Returns:
            推荐的环境模板列表，按兼容性降序。
        """
        # 按兼容性排序
        sorted_templates = sorted(
            templates,
            key=lambda x: float(x.get("compatibility", 0)),  # type: ignore[arg-type]
            reverse=True,
        )

        recommendations: list[Recommendation] = []
        for template in sorted_templates[:limit]:
            template_id = str(template.get("id", ""))
            template_name = str(template.get("name", ""))
            compatibility = float(template.get("compatibility", 0))
            recommendations.append(
                Recommendation(
                    id=template_id,
                    name=template_name,
                    score=compatibility,
                    reason=f"与 {agent_type} 类型兼容性 {compatibility:.0%}",
                )
            )

        return recommendations

    def recommend_scorers(
        self,
        case_features: dict[str, object],
        scorers: list[dict[str, object]],
        limit: int = 3,
    ) -> list[Recommendation]:
        """推荐评分器。

        Args:
            case_features: 用例特征。
            scorers: 可用评分器列表。
            limit: 返回数量限制。

        Returns:
            推荐的评分器列表，按相关性降序。
        """
        # 按相关性排序
        sorted_scorers = sorted(
            scorers,
            key=lambda x: float(x.get("relevance", 0)),  # type: ignore[arg-type]
            reverse=True,
        )

        recommendations: list[Recommendation] = []
        for scorer in sorted_scorers[:limit]:
            scorer_id = str(scorer.get("id", ""))
            scorer_name = str(scorer.get("name", ""))
            relevance = float(scorer.get("relevance", 0))
            recommendations.append(
                Recommendation(
                    id=scorer_id,
                    name=scorer_name,
                    score=relevance,
                    reason=f"与用例特征相关性 {relevance:.0%}",
                )
            )

        return recommendations
