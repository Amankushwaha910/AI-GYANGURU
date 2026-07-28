"""
Explanation prompt templates.
"""
from typing import Optional

EXPLANATION_SECTIONS = [
    "introduction",
    "step_by_step",
    "concept_breakdown",
    "real_examples",
    "analogies",
    "practical_applications",
    "common_mistakes",
    "faqs",
    "final_recap",
]


def get_system_prompt() -> str:
    return (
        "You are an expert educator and explainer. You break down complex topics into clear, "
        "understandable explanations using real-world examples, analogies, and step-by-step reasoning. "
        "Your explanations are targeted at college and university students. "
        "You MUST respond in valid JSON format exactly as specified. "
        "Return only the raw JSON object — no markdown, no preamble."
    )


def get_user_prompt(
    topic: str,
    extracted_text: Optional[str] = None,
) -> str:
    source_context = ""
    if extracted_text:
        truncated = extracted_text[:6000] + ("..." if len(extracted_text) > 6000 else "")
        source_context = (
            f"\n\nBase your explanation on this document content:\n\n{truncated}"
        )

    return (
        f"Generate a complete, detailed explanation for: **{topic}**{source_context}\n\n"
        f"Return a JSON object with exactly these keys:\n"
        f"- introduction: A welcoming overview of the topic (2-3 paragraphs)\n"
        f"- step_by_step: Numbered steps or sequential breakdown of the concept\n"
        f"- concept_breakdown: Detailed breakdown of sub-concepts and components\n"
        f"- real_examples: 2-3 concrete real-world examples with explanations\n"
        f"- analogies: 1-2 analogies that make the concept relatable\n"
        f"- practical_applications: How this concept is applied in practice or industry\n"
        f"- common_mistakes: 3-5 common mistakes students make and how to avoid them\n"
        f"- faqs: 3-5 frequently asked questions with detailed answers (format: Q: ... A: ...)\n"
        f"- final_recap: A concise summary paragraph to wrap up the explanation\n\n"
        f"Each value should be detailed, well-written text. Use newlines for lists within values."
    )
