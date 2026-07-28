"""
Centralized Prompt Builder.
All prompts are assembled here from versioned templates.
No prompt strings should exist outside this file or the templates directory.
"""
from typing import List, Optional

from app.ai.base import AIMessage
from app.ai.templates import (
    explanation_templates,
    quiz_templates,
    summary_templates,
)


class PromptBuilder:
    """
    Builds structured message lists for each AI module.
    Uses template functions to ensure consistent, versioned prompt formatting.
    """

    # ── Summary Prompts ───────────────────────────────────────────────────────

    def build_summary_prompt(
        self,
        topic: str,
        sections: List[str],
        extracted_text: Optional[str] = None,
    ) -> List[AIMessage]:
        """Build the prompt for summary generation."""
        system = summary_templates.get_system_prompt()
        user = summary_templates.get_user_prompt(
            topic=topic,
            sections=sections,
            extracted_text=extracted_text,
        )
        return [
            AIMessage(role="system", content=system),
            AIMessage(role="user", content=user),
        ]

    # ── Explanation Prompts ───────────────────────────────────────────────────

    def build_explanation_prompt(
        self,
        topic: str,
        extracted_text: Optional[str] = None,
    ) -> List[AIMessage]:
        """Build the prompt for explanation generation."""
        system = explanation_templates.get_system_prompt()
        user = explanation_templates.get_user_prompt(
            topic=topic,
            extracted_text=extracted_text,
        )
        return [
            AIMessage(role="system", content=system),
            AIMessage(role="user", content=user),
        ]

    # ── Quiz Prompts ──────────────────────────────────────────────────────────

    def build_quiz_prompt(
        self,
        topic: str,
        question_count: int,
        difficulty: str,
        category: Optional[str] = None,
        extracted_text: Optional[str] = None,
    ) -> List[AIMessage]:
        """Build the prompt for quiz generation."""
        system = quiz_templates.get_system_prompt()
        user = quiz_templates.get_user_prompt(
            topic=topic,
            question_count=question_count,
            difficulty=difficulty,
            category=category,
            extracted_text=extracted_text,
        )
        return [
            AIMessage(role="system", content=system),
            AIMessage(role="user", content=user),
        ]

    # ── Performance Summary Prompt ────────────────────────────────────────────

    def build_performance_summary_prompt(
        self,
        topic: str,
        score: int,
        total: int,
        wrong_categories: List[str],
        correct_categories: List[str],
    ) -> List[AIMessage]:
        """Build a short prompt to generate a quiz performance summary."""
        system = "You are an educational AI assistant. Provide concise, encouraging feedback."
        user = (
            f"A student just completed a quiz on '{topic}'. "
            f"They answered {score}/{total} questions correctly. "
            f"They struggled with: {', '.join(wrong_categories) or 'nothing specific'}. "
            f"They excelled at: {', '.join(correct_categories) or 'nothing specific'}. "
            f"Write a 2-3 sentence performance summary with specific improvement advice. "
            f"Be encouraging and actionable. Return plain text only."
        )
        return [
            AIMessage(role="system", content=system),
            AIMessage(role="user", content=user),
        ]


def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()
