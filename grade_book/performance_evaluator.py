from typing import Dict


class PerformanceEvaluator:
    """Single Responsibility - Handles performance evaluation logic"""

    def __init__(self, orchestration_engine):
        self.orchestration_engine = orchestration_engine

    def evaluate(self) -> Dict:
        engine_data = self.orchestration_engine.process_question()
        performance_stats = engine_data["performance_stats"]
        ai_recommendations = engine_data["ai_recommendations"]
        has_failed = any(status == "incomplete" for status in performance_stats.difficulty_status.values())
        return {
            "has_failed": has_failed,
            "ai_recommendations": ai_recommendations,
            "performance_stats": performance_stats,
        }
