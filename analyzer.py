"""
Response Analyzer and Report Generator

This module provides additional analysis capabilities for the diagnostic responses,
including detailed scoring, benchmarking, and report generation.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from diagnostic_questions import diagnostic_questionnaire, DiagnosticQuestion
from moonshot_client import get_moonshot_client

logger = logging.getLogger(__name__)


@dataclass
class TimeSavingRecommendation:
    """Represents a time-saving opportunity with quantified benefits."""
    area: str
    current_time_weekly: float  # Hours currently spent per week
    optimized_time_weekly: float  # Hours after optimization
    time_savings: float  # Net time saved per week
    implementation_time: str  # Easy, Medium, Hard
    estimated_cost: str  # Cost range
    priority: str  # High, Medium, Low
    description: str
    specific_actions: List[str]


class PracticeAnalyzer:
    """Analyzes diagnostic responses to identify optimization opportunities."""

    def __init__(self):
        self.questionnaire = diagnostic_questionnaire

    def analyze_responses_detailed(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """
        Perform detailed analysis of responses to identify specific opportunities.

        Args:
            responses: Dictionary mapping question_id to selected option_id

        Returns:
            Detailed analysis including scores, recommendations, and time savings
        """
        # Calculate base scores
        score_results = self.questionnaire.calculate_score(responses)

        # Analyze each category for specific opportunities
        category_analysis = self._analyze_categories(responses, score_results)

        # Calculate time savings based on responses
        time_savings = self._calculate_time_savings(responses, score_results)

        # Generate prioritized recommendations
        recommendations = self._generate_recommendations(responses, time_savings)

        # Create benchmark comparison
        benchmark = self._compare_to_benchmarks(score_results)

        return {
            "score_results": score_results,
            "category_analysis": category_analysis,
            "time_savings": time_savings,
            "recommendations": recommendations,
            "benchmark": benchmark,
            "analysis_timestamp": datetime.now().isoformat()
        }

    def _analyze_categories(self, responses: Dict[str, str], score_results: Dict) -> Dict[str, Any]:
        """Analyze each category for specific issues."""
        category_analysis = {}

        for category in self.questionnaire.categories.keys():
            percentage = score_results["category_percentages"][category]
            count = score_results["category_counts"][category]

            if count == 0:
                continue

            # Determine severity based on percentage
            if percentage >= 70:
                severity = "Good"
                priority = "Low"
            elif percentage >= 50:
                severity = "Needs Improvement"
                priority = "Medium"
            else:
                severity = "Critical"
                priority = "High"

            # Get specific issues in this category
            questions_in_cat = self.questionnaire.get_questions_by_category(category)
            low_scoring = []

            for question in questions_in_cat:
                if question.id in responses:
                    try:
                        option = next(opt for opt in question.options if opt.id == responses[question.id])
                        if option.value <= 2:  # Low scoring response
                            low_scoring.append({
                                "question": question.question_text,
                                "issue": self._identify_issue(question, option)
                            })
                    except StopIteration:
                        continue

            category_analysis[category] = {
                "severity": severity,
                "priority": priority,
                "percentage": percentage,
                "question_count": count,
                "low_scoring_areas": low_scoring
            }

        return category_analysis

    def _identify_issue(self, question: DiagnosticQuestion, option: Any) -> str:
        """Identify the specific issue based on question and low-scoring option."""
        issue_map = {
            "intake": "Inefficient client intake process",
            "documents": "Manual document creation",
            "case_management": "Poor deadline/case tracking",
            "billing": "Inefficient billing practices",
            "admin": "Excessive administrative burden",
            "pain_points": "Identified workflow bottleneck"
        }
        return issue_map.get(question.category, "Workflow inefficiency")

    def _calculate_time_savings(self, responses: Dict[str, str], score_results: Dict) -> List[TimeSavingRecommendation]:
        """Calculate potential time savings for each area."""
        time_savings = []

        # Define typical time allocations for litigation practices
        time_allocations = {
            "intake": {"weekly": 8, "description": "hours spent on intake"},
            "documents": {"weekly": 12, "description": "hours on document drafting"},
            "case_management": {"weekly": 6, "description": "hours on case/deadline tracking"},
            "billing": {"weekly": 4, "description": "hours on billing/time tracking"},
            "admin": {"weekly": 10, "description": "hours on administrative tasks"}
        }

        for category, data in time_allocations.items():
            percentage = score_results["category_percentages"].get(category, 0)

            # Estimate time waste based on score
            # Low score (0-40%) = high waste (70% of time wasted)
            # Medium score (40-70%) = moderate waste (40% wasted)
            # High score (70%+) = low waste (15% wasted)
            if percentage < 40:
                waste_factor = 0.7
                optimization_factor = 0.6  # Can save 60% of wasted time
            elif percentage < 70:
                waste_factor = 0.4
                optimization_factor = 0.5
            else:
                waste_factor = 0.15
                optimization_factor = 0.4

            current_waste = data["weekly"] * waste_factor
            potential_savings = current_waste * optimization_factor

            if potential_savings > 0.5:  # Only include if at least 30 minutes per week
                # Determine implementation difficulty
                if percentage < 30:
                    difficulty = "Hard"
                    cost = "$500-2000"
                elif percentage < 50:
                    difficulty = "Medium"
                    cost = "$200-500"
                else:
                    difficulty = "Easy"
                    cost = "$0-200"

                recommendation = TimeSavingRecommendation(
                    area=self.questionnaire.categories[category],
                    current_time_weekly=data["weekly"],
                    optimized_time_weekly=data["weekly"] - potential_savings,
                    time_savings=potential_savings,
                    implementation_time=difficulty,
                    estimated_cost=cost,
                    priority="High" if potential_savings > 2 else "Medium",
                    description=f"Optimize {data['description']} through automation and better systems",
                    specific_actions=self._get_specific_actions(category, percentage)
                )
                time_savings.append(recommendation)

        return sorted(time_savings, key=lambda x: x.time_savings, reverse=True)

    def _get_specific_actions(self, category: str, percentage: float) -> List[str]:
        """Get specific action steps for each category."""
        actions = {
            "intake": [
                "Implement online intake forms",
                "Create automated conflict checking",
                "Set up client portal for document sharing"
            ],
            "documents": [
                "Create document templates for common pleadings",
                "Implement document automation software",
                "Build clause library for frequently used language"
            ],
            "case_management": [
                "Implement practice management software",
                "Set up automatic deadline calculations",
                "Create task templates for case phases"
            ],
            "billing": [
                "Use time tracking software",
                "Automate invoice generation",
                "Implement online payment processing"
            ],
            "admin": [
                "Delegate routine tasks to support staff",
                "Use email templates",
                "Implement scheduling software"
            ]
        }

        return actions.get(category, ["Evaluate current processes", "Research automation options", "Implement improvements"])

    def _generate_recommendations(self, responses: Dict[str, str], time_savings: List[TimeSavingRecommendation]) -> Dict[str, Any]:
        """Generate prioritized recommendations."""
        if not time_savings:
            return {
                "quick_wins": [],
                "short_term": [],
                "long_term": [],
                "total_weekly_savings": 0
            }

        # Categorize by implementation timeline
        quick_wins = [r for r in time_savings if r.implementation_time == "Easy"]
        short_term = [r for r in time_savings if r.implementation_time == "Medium"]
        long_term = [r for r in time_savings if r.implementation_time == "Hard"]

        total_savings = sum(r.time_savings for r in time_savings)

        return {
            "quick_wins": quick_wins[:3],  # Top 3 quick wins
            "short_term": short_term[:3],
            "long_term": long_term[:2],
            "total_weekly_savings": total_savings
        }

    def _compare_to_benchmarks(self, score_results: Dict) -> Dict[str, Any]:
        """Compare scores to industry benchmarks."""
        overall_score = score_results["overall_percentage"]

        # Define benchmarks (these would be based on real data in production)
        benchmarks = {
            "solo_litigation_minimal_tech": {"avg": 45, "good": 60, "excellent": 75},
            "solo_litigation_moderate_tech": {"avg": 60, "good": 75, "excellent": 85},
        }

        # Use solo litigation with minimal tech as baseline
        benchmark = benchmarks["solo_litigation_minimal_tech"]

        if overall_score >= benchmark["excellent"]:
            relative_performance = "Excellent"
        elif overall_score >= benchmark["good"]:
            relative_performance = "Good"
        elif overall_score >= benchmark["avg"]:
            relative_performance = "Average"
        else:
            relative_performance = "Below Average"

        return {
            "relative_performance": relative_performance,
            "benchmark_avg": benchmark["avg"],
            "your_score": overall_score,
            "comparison": "Compared to similar practices (solo litigation, minimal tech use)"
        }

    def generate_executive_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate an executive summary for the report."""
        score = analysis["score_results"]["overall_percentage"]
        grade = self.questionnaire.get_optimization_grade(score)
        total_savings = analysis["recommendations"]["total_weekly_savings"]

        summary_parts = [
            f"Based on your responses, your practice optimization score is {score:.1f}% ({grade}).",
            f"",
            f"Key Findings:",
        ]

        # Add category-specific insights
        for category, data in analysis["category_analysis"].items():
            if data["priority"] in ["High", "Medium"]:
                cat_name = self.questionnaire.categories[category]
                summary_parts.append(f"• {cat_name}: {data['severity']} ({data['percentage']:.1f}%)")

        summary_parts.extend([
            f"",
            f"Opportunities:",
            f"• Potential time savings: {total_savings:.1f} hours per week",
            f"• Quick wins identified: {len(analysis['recommendations']['quick_wins'])}",
            f"• Implementation timeline: Varies from immediate to 90 days"
        ])

        return "\n".join(summary_parts)

    def export_report_data(self, analysis: Dict[str, Any], lawyer_name: str) -> str:
        """Export analysis data as JSON for external use."""
        export_data = {
            "lawyer_name": lawyer_name,
            "analysis_date": analysis["analysis_timestamp"],
            "overall_score": analysis["score_results"]["overall_percentage"],
            "grade": self.questionnaire.get_optimization_grade(analysis["score_results"]["overall_percentage"]),
            "category_scores": {
                cat: {
                    "percentage": data["percentage"],
                    "severity": data["severity"],
                    "priority": data["priority"]
                }
                for cat, data in analysis["category_analysis"].items()
            },
            "time_savings": {
                "total_weekly_hours": analysis["recommendations"]["total_weekly_savings"],
                "monthly_hours": analysis["recommendations"]["total_weekly_savings"] * 4.33,
                "yearly_hours": analysis["recommendations"]["total_weekly_savings"] * 52
            },
            "recommendations_count": {
                "quick_wins": len(analysis["recommendations"]["quick_wins"]),
                "short_term": len(analysis["recommendations"]["short_term"]),
                "long_term": len(analysis["recommendations"]["long_term"])
            }
        }

        return json.dumps(export_data, indent=2)


# Global instance
practice_analyzer = PracticeAnalyzer()


def analyze_responses(responses: Dict[str, str]) -> Dict[str, Any]:
    """Convenience function to analyze responses."""
    return practice_analyzer.analyze_responses_detailed(responses)
