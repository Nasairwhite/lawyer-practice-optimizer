"""
Moonshot AI API Client for Lawyer Practice Optimization

This module handles all interactions with the Moonshot AI API (Kimi model)
for providing intelligent guidance during the diagnostic process.
"""

import os
import logging
from typing import Dict, List, Optional, Iterator
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MoonshotClient:
    """Client for interacting with Moonshot AI's Kimi model."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Moonshot AI client.

        Args:
            api_key: Moonshot AI API key. If not provided, will use MOONSHOT_API_KEY env var.

        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")

        if not self.api_key:
            raise ValueError("Moonshot API key not found. Set MOONSHOT_API_KEY environment variable.")

        # Moonshot AI uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        )

        # Model configuration
        self.model = "moonshot-v1-8k"  # 8k context window for cost efficiency
        self.temperature = 0.3  # Lower temperature for more consistent guidance
        self.max_tokens = 1000

    def get_question_guidance(self, question_text: str, practice_area: str) -> str:
        """
        Generate AI guidance for a diagnostic question.

        Args:
            question_text: The diagnostic question being asked.
            practice_area: The lawyer's practice area (e.g., "litigation").

        Returns:
            AI-generated guidance text to help the lawyer understand the question.
        """
        system_prompt = self._build_guidance_system_prompt(practice_area)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate helpful guidance for this question: {question_text}"}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            guidance = response.choices[0].message.content.strip()
            logger.info(f"Generated guidance for question: {question_text[:50]}...")
            return guidance

        except Exception as e:
            logger.error(f"Error generating guidance: {e}")
            return self._get_default_guidance(question_text)

    def analyze_responses(self, responses: Dict[str, str], practice_area: str) -> Dict:
        """
        Analyze the lawyer's responses and generate recommendations.

        Args:
            responses: Dictionary of question_id to answer.
            practice_area: The lawyer's practice area.

        Returns:
            Dictionary containing analysis and recommendations.
        """
        system_prompt = self._build_analysis_system_prompt(practice_area)

        # Format responses for the AI
        formatted_responses = self._format_responses_for_analysis(responses)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": formatted_responses}
                ],
                temperature=0.2,  # Lower temperature for analysis
                max_tokens=2000
            )

            analysis = response.choices[0].message.content.strip()
            logger.info(f"Generated analysis for {len(responses)} responses")

            return self._parse_analysis(analysis)

        except Exception as e:
            logger.error(f"Error analyzing responses: {e}")
            return {"error": "Analysis failed", "recommendations": []}

    def generate_report_summary(self, analysis_results: Dict, lawyer_name: str) -> str:
        """
        Generate a final report summary for the lawyer.

        Args:
            analysis_results: Results from the analysis phase.
            lawyer_name: Name of the lawyer.

        Returns:
            Formatted report summary.
        """
        system_prompt = self._build_report_system_prompt()

        formatted_results = self._format_results_for_report(analysis_results)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a report for {lawyer_name} based on: {formatted_results}"}
                ],
                temperature=0.3,
                max_tokens=2500
            )

            report = response.choices[0].message.content.strip()
            logger.info(f"Generated report for {lawyer_name}")
            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return self._get_default_report(lawyer_name, analysis_results)

    def _build_guidance_system_prompt(self, practice_area: str) -> str:
        """Build system prompt for question guidance."""
        return f"""You are an expert legal practice management consultant specializing in {practice_area}.
Your role is to help lawyers identify opportunities to optimize their practice through technology and automation.

For each diagnostic question you are given, provide:
1. Brief context about why this question matters
2. What to consider when answering
3. Examples or clarification if helpful
4. Keep it concise (2-4 sentences)

Focus on practical, actionable insights that will help the lawyer provide accurate responses.
Be encouraging and professional in tone.

Practice Area: {practice_area}"""

    def _build_analysis_system_prompt(self, practice_area: str) -> str:
        """Build system prompt for response analysis."""
        return f"""You are an expert legal practice management consultant with 20+ years of experience optimizing law practices.
You specialize in identifying inefficiencies and implementing automation solutions for {practice_area} practices.

Your task is to analyze a lawyer's responses to diagnostic questions and:

1. Identify the 3-5 biggest time-wasters and inefficiencies
2. Calculate estimated time savings (in hours per week) for each recommended optimization
3. Prioritize recommendations by impact and ease of implementation
4. Provide specific, actionable steps for each recommendation
5. Consider the lawyer's stated tech comfort level (minimal tech use)

For each recommendation, include:
- Specific problem identified
- Proposed solution/tool/process change
- Estimated weekly time savings
- Implementation difficulty (Easy/Medium/Hard)
- Estimated cost (if applicable)
- Quick wins vs long-term improvements

Format your response as a structured analysis with clear sections.
Focus on practical solutions suitable for a litigation practice with minimal current technology use.

Practice Area: {practice_area}"""

    def _build_report_system_prompt(self) -> str:
        """Build system prompt for report generation."""
        return """You are an expert legal practice management consultant preparing a final report for a lawyer.

Create a professional, actionable report that:

1. Begins with an executive summary of findings
2. Lists 5-7 prioritized recommendations with specific details
3. Includes a "Quick Wins" section (things they can implement in 1-2 weeks)
4. Provides a 90-day implementation roadmap
5. Includes estimated time savings for each phase
6. Addresses potential concerns or barriers
7. Ends with next steps

Make the report:
- Professional but not overly formal
- Action-oriented and specific
- Sensitive to the fact that this is a consultation to help them save time
- Realistic about implementation challenges
- Clear about ROI and benefits

Format with clear headings, bullet points, and make it easy to scan.
Length: Approximately 800-1200 words."""

    def _format_responses_for_analysis(self, responses: Dict[str, str]) -> str:
        """Format responses for analysis."""
        formatted = "Diagnostic Questionnaire Responses:\n\n"
        for q_id, answer in responses.items():
            formatted += f"{q_id}: {answer}\n"
        return formatted

    def _format_results_for_report(self, analysis_results: Dict) -> str:
        """Format analysis results for report generation."""
        return str(analysis_results)

    def _parse_analysis(self, analysis_text: str) -> Dict:
        """Parse the AI analysis into a structured dictionary."""
        # This is a simplified parser - could be enhanced with more sophisticated parsing
        return {
            "raw_analysis": analysis_text,
            "recommendations": ["Recommendation parsing would go here"],
            "time_savings": "Estimated time savings would be calculated here"
        }

    def _get_default_guidance(self, question_text: str) -> str:
        """Return default guidance if AI fails."""
        return f"This question helps us understand your current process for: {question_text[:60]}... Consider your typical workflow when answering."

    def _get_default_report(self, lawyer_name: str, analysis_results: Dict) -> str:
        """Return default report if AI fails."""
        return f"""# Practice Optimization Report for {lawyer_name}

## Executive Summary
Unfortunately, we encountered an issue generating your personalized report. However, based on your responses, here are general recommendations for litigation practices:

## Key Recommendations
1. **Document Automation** - Implement templates for common pleadings and motions
2. **Case Management System** - Track deadlines and tasks in one place
3. **Billing Software** - Automate time tracking and invoicing
4. **Client Communication** - Use portals to reduce email back-and-forth

Please contact us for a more detailed analysis.
"""


# Global instance for easy access
_moonshot_client_instance = None


def get_moonshot_client() -> MoonshotClient:
    """Get or create the global Moonshot client instance."""
    global _moonshot_client_instance

    if _moonshot_client_instance is None:
        _moonshot_client_instance = MoonshotClient()

    return _moonshot_client_instance
