"""智能推荐功能测试。"""

from __future__ import annotations

import pytest

from agenttest.modules.test_agent.domain.recommender import (
    Recommender,
    Recommendation,
)


class TestRecommender:
    """推荐器测试。"""

    @pytest.fixture()
    def recommender(self) -> Recommender:
        """创建推荐器实例。"""
        return Recommender()

    def test_recommend_test_sets(self, recommender: Recommender) -> None:
        """测试推荐测试集。"""
        agent_type = "chat"
        history = [
            {"test_set_id": "set-1", "success_rate": 0.9},
            {"test_set_id": "set-2", "success_rate": 0.7},
            {"test_set_id": "set-3", "success_rate": 0.95},
        ]
        recommendations = recommender.recommend_test_sets(agent_type, history)
        assert len(recommendations) <= 3
        assert recommendations[0].id == "set-3"

    def test_recommend_environment_templates(
        self, recommender: Recommender
    ) -> None:
        """测试推荐环境模板。"""
        agent_type = "chat"
        templates = [
            {"id": "env-1", "name": "生产环境", "compatibility": 0.8},
            {"id": "env-2", "name": "测试环境", "compatibility": 0.95},
            {"id": "env-3", "name": "开发环境", "compatibility": 0.6},
        ]
        recommendations = recommender.recommend_environment_templates(
            agent_type, templates
        )
        assert len(recommendations) <= 3
        assert recommendations[0].id == "env-2"

    def test_recommend_scorers(self, recommender: Recommender) -> None:
        """测试推荐评分器。"""
        case_features = {"type": "qa", "complexity": "high"}
        scorers = [
            {"id": "scorer-1", "name": "准确性", "relevance": 0.9},
            {"id": "scorer-2", "name": "质量", "relevance": 0.7},
            {"id": "scorer-3", "name": "安全性", "relevance": 0.5},
        ]
        recommendations = recommender.recommend_scorers(case_features, scorers)
        assert len(recommendations) <= 3
        assert recommendations[0].id == "scorer-1"

    def test_empty_history_returns_empty(
        self, recommender: Recommender
    ) -> None:
        """测试空历史返回空推荐。"""
        recommendations = recommender.recommend_test_sets("chat", [])
        assert len(recommendations) == 0

    def test_recommendations_sorted_by_score(
        self, recommender: Recommender
    ) -> None:
        """测试推荐按分数排序。"""
        history = [
            {"test_set_id": "set-1", "success_rate": 0.7},
            {"test_set_id": "set-2", "success_rate": 0.9},
            {"test_set_id": "set-3", "success_rate": 0.8},
        ]
        recommendations = recommender.recommend_test_sets("chat", history)
        scores = [r.score for r in recommendations]
        assert scores == sorted(scores, reverse=True)
