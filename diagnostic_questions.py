"""
Diagnostic Questions Library for Lawyer Practice Optimization

This module contains the comprehensive diagnostic questionnaire designed to
identify optimization opportunities in a litigation practice.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class QuestionOption:
    """Represents a multiple choice option for a diagnostic question."""
    id: str
    text: str
    value: int  # Score weight for this option
    custom_input: bool = False  # Whether option D allows custom text input


@dataclass
class DiagnosticQuestion:
    """Represents a diagnostic question with multiple choice options."""
    id: str
    category: str
    question_text: str
    options: List[QuestionOption]


class DiagnosticQuestionnaire:
    """Manages the diagnostic question set for litigation practices."""

    def __init__(self):
        self.questions = self._load_questions()
        self.categories = {
            "intake": "Client Intake & Management",
            "documents": "Document Drafting & Templates",
            "case_management": "Case & Deadline Management",
            "billing": "Billing & Time Tracking",
            "admin": "Administrative Tasks",
            "pain_points": "Pain Points & Bottlenecks"
        }

    def _load_questions(self) -> List[DiagnosticQuestion]:
        """Load all diagnostic questions."""
        return [
            # CLIENT INTAKE & MANAGEMENT
            DiagnosticQuestion(
                id="intake_1",
                category="intake",
                question_text="How do you currently handle new client inquiries and intake?",
                options=[
                    QuestionOption("intake_1_a", "I respond to emails/calls individually and manually track everything in a notebook or basic spreadsheet", 1),
                    QuestionOption("intake_1_b", "I have some templates but still do most intake manually with email and calendar", 2),
                    QuestionOption("intake_1_c", "I use a practice management system with automated intake forms and conflict checking", 4),
                    QuestionOption("intake_1_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="intake_2",
                category="intake",
                question_text="What happens when a potential conflict of interest needs to be checked?",
                options=[
                    QuestionOption("intake_2_a", "I manually search through files, emails, and my memory", 1),
                    QuestionOption("intake_2_b", "I have a basic list but it's not comprehensive", 2),
                    QuestionOption("intake_2_c", "I use software that automatically checks conflicts across all matters", 4),
                    QuestionOption("intake_2_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="intake_3",
                category="intake",
                question_text="How do you track communications with clients (emails, calls, meetings)?",
                options=[
                    QuestionOption("intake_3_a", "I rely on memory and occasionally write notes", 1),
                    QuestionOption("intake_3_b", "I manually log important communications in a Word doc or spreadsheet", 2),
                    QuestionOption("intake_3_c", "All communications are automatically logged and linked to case files", 4),
                    QuestionOption("intake_3_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="intake_4",
                category="intake",
                question_text="How many hours per week do you spend on the phone with clients answering basic questions about their case status?",
                options=[
                    QuestionOption("intake_4_a", "Less than 1 hour", 4),
                    QuestionOption("intake_4_b", "1-3 hours", 3),
                    QuestionOption("intake_4_c", "3-5 hours", 2),
                    QuestionOption("intake_4_d", "More than 5 hours", 1)
                ]
            ),

            # DOCUMENT DRAFTING & TEMPLATES
            DiagnosticQuestion(
                id="docs_1",
                category="documents",
                question_text="How do you currently draft routine legal documents (motions, pleadings, discovery requests)?",
                options=[
                    QuestionOption("docs_1_a", "I start from scratch or copy-paste from old documents each time", 1),
                    QuestionOption("docs_1_b", "I have some templates but customize them heavily each time", 2),
                    QuestionOption("docs_1_c", "I use document automation software with smart templates that auto-fill case details", 4),
                    QuestionOption("docs_1_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="docs_2",
                category="documents",
                question_text="When you need to find a specific clause or language you've used before, how do you locate it?",
                options=[
                    QuestionOption("docs_2_a", "I search through old documents manually or try to remember which case it was in", 1),
                    QuestionOption("docs_2_b", "I have some favorite documents I keep referring back to", 2),
                    QuestionOption("docs_2_c", "I use a clause library or document management system with full-text search", 4),
                    QuestionOption("docs_2_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="docs_3",
                category="documents",
                question_text="How much time do you spend formatting documents to meet court requirements?",
                options=[
                    QuestionOption("docs_3_a", "I manually format each document and check court rules frequently", 1),
                    QuestionOption("docs_3_b", "I have some basic templates but still spend time on formatting", 2),
                    QuestionOption("docs_3_c", "Templates automatically apply correct formatting and court rules", 4),
                    QuestionOption("docs_3_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="docs_4",
                category="documents",
                question_text="How do you handle document assembly for cases with multiple similar pleadings (e.g., multiple defendants)?",
                options=[
                    QuestionOption("docs_4_a", "I manually customize each document individually", 1),
                    QuestionOption("docs_4_b", "I use find-and-replace across documents", 2),
                    QuestionOption("docs_4_c", "I use document automation that auto-generates variations", 4),
                    QuestionOption("docs_4_d", "", 3, custom_input=True)
                ]
            ),

            # CASE & DEADLINE MANAGEMENT
            DiagnosticQuestion(
                id="case_1",
                category="case_management",
                question_text="How do you track court deadlines, filing dates, and statute of limitations?",
                options=[
                    QuestionOption("case_1_a", "I use a paper calendar and manually calculate deadlines", 1),
                    QuestionOption("case_1_b", "I use Outlook/Google Calendar with manual entries", 2),
                    QuestionOption("case_1_c", "I use practice management software with automatic deadline calculation and alerts", 4),
                    QuestionOption("case_1_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="case_2",
                category="case_management",
                question_text="What happens when a court date gets continued or changed?",
                options=[
                    QuestionOption("case_2_a", "I manually update my calendar and try to remember to notify everyone", 1),
                    QuestionOption("case_2_b", "I update my calendar but sometimes forget to notify all parties", 2),
                    QuestionOption("case_2_c", "My system automatically updates and notifies relevant parties", 4),
                    QuestionOption("case_2_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="case_3",
                category="case_management",
                question_text="How do you track tasks and to-dos across all your active cases?",
                options=[
                    QuestionOption("case_3_a", "I keep separate lists or rely on memory", 1),
                    QuestionOption("case_3_b", "I have a master to-do list but it's not linked to specific cases", 2),
                    QuestionOption("case_3_c", "All tasks are tracked in a case management system with automatic reminders", 4),
                    QuestionOption("case_3_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="case_4",
                category="case_management",
                question_text="When you need to find a specific document or piece of information for a case, how quickly can you locate it?",
                options=[
                    QuestionOption("case_4_a", "It often takes 15+ minutes of searching through emails, files, and notes", 1),
                    QuestionOption("case_4_b", "Usually 5-10 minutes - I have some organization but it's inconsistent", 2),
                    QuestionOption("case_4_c", "I can find almost anything in under 2 minutes with my case management system", 4),
                    QuestionOption("case_4_d", "", 3, custom_input=True)
                ]
            ),

            # BILLING & TIME TRACKING
            DiagnosticQuestion(
                id="billing_1",
                category="billing",
                question_text="How do you track billable time?",
                options=[
                    QuestionOption("billing_1_a", "I try to reconstruct it at the end of the day or week from memory", 1),
                    QuestionOption("billing_1_b", "I manually log time in a spreadsheet throughout the day", 2),
                    QuestionOption("billing_1_c", "I use time-tracking software that integrates with my billing system", 4),
                    QuestionOption("billing_1_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="billing_2",
                category="billing",
                question_text="How long does it take you to prepare and send invoices each month?",
                options=[
                    QuestionOption("billing_2_a", "Less than 1 hour", 4),
                    QuestionOption("billing_2_b", "1-2 hours", 3),
                    QuestionOption("billing_2_c", "2-5 hours", 2),
                    QuestionOption("billing_2_d", "More than 5 hours", 1)
                ]
            ),
            DiagnosticQuestion(
                id="billing_3",
                category="billing",
                question_text="How often do you miss billable time because you forget to record it?",
                options=[
                    QuestionOption("billing_3_a", "Frequently - I probably lose several hours per week", 1),
                    QuestionOption("billing_3_b", "Sometimes - maybe 1-2 hours per week", 2),
                    QuestionOption("billing_3_c", "Rarely - I track almost everything", 4),
                    QuestionOption("billing_3_d", "", 3, custom_input=True)
                ]
            ),

            # ADMINISTRATIVE TASKS
            DiagnosticQuestion(
                id="admin_1",
                category="admin",
                question_text="How much time do you spend on administrative tasks (scheduling, emails, filing, etc.) each week?",
                options=[
                    QuestionOption("admin_1_a", "Less than 5 hours", 4),
                    QuestionOption("admin_1_b", "5-10 hours", 3),
                    QuestionOption("admin_1_c", "10-15 hours", 2),
                    QuestionOption("admin_1_d", "More than 15 hours", 1)
                ]
            ),
            DiagnosticQuestion(
                id="admin_2",
                category="admin",
                question_text="Do you have support staff (paralegal, assistant) to help with administrative work?",
                options=[
                    QuestionOption("admin_2_a", "No, I handle everything myself", 1),
                    QuestionOption("admin_2_b", "Yes, but they're overloaded and I still do a lot myself", 2),
                    QuestionOption("admin_2_c", "Yes, and we have efficient systems for delegation", 4),
                    QuestionOption("admin_2_d", "", 3, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="admin_3",
                category="admin",
                question_text="How much time do you spend after hours or on weekends catching up on work?",
                options=[
                    QuestionOption("admin_3_a", "Rarely - I mostly work during business hours", 4),
                    QuestionOption("admin_3_b", "1-3 hours per week", 3),
                    QuestionOption("admin_3_c", "3-7 hours per week", 2),
                    QuestionOption("admin_3_d", "More than 7 hours per week", 1)
                ]
            ),

            # PAIN POINTS & BOTTLENECKS
            DiagnosticQuestion(
                id="pain_1",
                category="pain_points",
                question_text="What is your biggest frustration or time-waster in your practice?",
                options=[
                    QuestionOption("pain_1_a", "Constant interruptions from clients asking for status updates", 1),
                    QuestionOption("pain_1_b", "Spending too much time on administrative tasks instead of billable work", 2),
                    QuestionOption("pain_1_c", "Document drafting and customization takes forever", 3),
                    QuestionOption("pain_1_d", "", 4, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="pain_2",
                category="pain_points",
                question_text="How often do you miss deadlines or have close calls?",
                options=[
                    QuestionOption("pain_2_a", "Never - I have a reliable system", 4),
                    QuestionOption("pain_2_b", "Rarely - maybe once or twice per year", 3),
                    QuestionOption("pain_2_c", "Occasionally - a few times per year", 2),
                    QuestionOption("pain_2_d", "More often than I'd like to admit", 1)
                ]
            ),
            DiagnosticQuestion(
                id="pain_3",
                category="pain_points",
                question_text="What would you do with an extra 5-10 hours per week?",
                options=[
                    QuestionOption("pain_3_a", "Take on more cases/clients to grow my practice", 1),
                    QuestionOption("pain_3_b", "Focus on higher-value work and case strategy", 2),
                    QuestionOption("pain_3_c", "Improve work-life balance and reduce stress", 3),
                    QuestionOption("pain_3_d", "", 4, custom_input=True)
                ]
            ),
            DiagnosticQuestion(
                id="pain_4",
                category="pain_points",
                question_text="If you could automate one task in your practice, what would it be?",
                options=[
                    QuestionOption("pain_4_a", "Client intake and initial document gathering", 1),
                    QuestionOption("pain_4_b", "Document drafting and assembly", 2),
                    QuestionOption("pain_4_c", "Billing and time tracking", 3),
                    QuestionOption("pain_4_d", "", 4, custom_input=True)
                ]
            )
        ]

    def get_all_questions(self) -> List[DiagnosticQuestion]:
        """Get all diagnostic questions."""
        return self.questions

    def get_questions_by_category(self, category: str) -> List[DiagnosticQuestion]:
        """Get questions for a specific category."""
        return [q for q in self.questions if q.category == category]

    def get_question_by_id(self, question_id: str) -> DiagnosticQuestion:
        """Get a specific question by ID."""
        for question in self.questions:
            if question.id == question_id:
                return question
        raise ValueError(f"Question with ID {question_id} not found")

    def calculate_score(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate scores based on responses.

        Args:
            responses: Dictionary mapping question_id to selected option_id

        Returns:
            Dictionary with category scores and total score
        """
        category_scores = {cat: 0 for cat in self.categories.keys()}
        category_counts = {cat: 0 for cat in self.categories.keys()}
        total_score = 0
        max_possible = 0

        for question_id, option_id in responses.items():
            try:
                question = self.get_question_by_id(question_id)
                selected_option = next(opt for opt in question.options if opt.id == option_id)

                category_scores[question.category] += selected_option.value
                category_counts[question.category] += 1
                total_score += selected_option.value
                max_possible += 4  # Assuming max value is 4 for all questions
            except (ValueError, StopIteration):
                # Skip invalid responses
                continue

        # Calculate percentages
        category_percentages = {}
        for cat in self.categories.keys():
            if category_counts[cat] > 0:
                category_percentages[cat] = (category_scores[cat] / (category_counts[cat] * 4)) * 100
            else:
                category_percentages[cat] = 0

        overall_percentage = (total_score / max_possible * 100) if max_possible > 0 else 0

        return {
            "category_scores": category_scores,
            "category_counts": category_counts,
            "category_percentages": category_percentages,
            "total_score": total_score,
            "max_possible": max_possible,
            "overall_percentage": overall_percentage
        }

    def get_optimization_grade(self, percentage: float) -> str:
        """
        Convert percentage to optimization grade.

        Args:
            percentage: Overall optimization percentage (0-100)

        Returns:
            Grade: A (optimized), B (good), C (needs work), D (inefficient), F (critical)
        """
        if percentage >= 85:
            return "A - Highly Optimized"
        elif percentage >= 70:
            return "B - Well Organized"
        elif percentage >= 55:
            return "C - Needs Improvement"
        elif percentage >= 40:
            return "D - Inefficient"
        else:
            return "F - Critical Issues"


# Global instance
diagnostic_questionnaire = DiagnosticQuestionnaire()
