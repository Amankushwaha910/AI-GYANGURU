"""
Summary prompt templates — versioned and centralized.
"""
from typing import List, Optional


SECTION_INSTRUCTIONS = {
    "definition": "**Definition**: A clear, precise definition of the topic.",
    "key_concepts": "**Key Concepts**: Bullet-point list of the most important concepts (minimum 5).",
    "important_facts": "**Important Facts**: Numbered list of must-know facts.",
    "formula_sheet": "**Formula Sheet**: All relevant formulas with variable explanations.",
    "mnemonics": "**Mnemonics**: Memory tricks, acronyms, or visual associations to remember key points.",
    "exam_tips": "**Exam Tips**: Specific advice for scoring well in exams on this topic.",
    "revision_notes": "**Revision Notes**: Concise paragraph-form revision notes covering the full topic.",
    "checklist": "**Checklist**: A checklist of things a student must know before their exam.",
}


def get_system_prompt() -> str:
    return (
        "You are an expert educational content generator specializing in creating structured, "
        "accurate, and student-friendly learning materials. Your outputs are always well-organized, "
        "factually correct, and optimized for exam preparation. "
        "You MUST respond in valid JSON format exactly as specified in the user prompt. "
        "Do not add markdown code blocks, explanations outside the JSON, or any preamble. "
        "Return only the raw JSON object."
    )


def get_user_prompt(
    topic: str,
    sections: List[str],
    extracted_text: Optional[str] = None,
) -> str:
    section_instructions = "\n".join(
        f"- {SECTION_INSTRUCTIONS.get(s, s)}" for s in sections
    )

    source_context = ""
    if extracted_text:
        # Truncate to avoid exceeding context limits
        truncated = extracted_text[:6000] + ("..." if len(extracted_text) > 6000 else "")
        source_context = (
            f"\n\nUse the following document content as the PRIMARY source for your summary. "
            f"Only use your training knowledge to fill gaps:\n\n{truncated}"
        )

    json_keys = {s: "string with content" for s in sections}

    return (
        f"Generate a comprehensive study summary for the topic: **{topic}**{source_context}\n\n"
        f"Include ONLY these sections:\n{section_instructions}\n\n"
        f"Respond with a JSON object where keys match exactly these section names: {list(sections)}\n"
        f"Each value should be detailed, well-formatted text appropriate for student study.\n"
        f"Use newlines within values for lists and structure.\n\n"
        f"Example format:\n{json_keys}"
    )
