"""
Quiz prompt templates.
"""
from typing import Optional


def get_system_prompt() -> str:
    return (
        "You are an expert quiz generator for educational assessments. "
        "You create high-quality, accurate multiple-choice questions that test genuine understanding. "
        "Questions must have exactly 4 options, one clearly correct answer, and a detailed explanation. "
        "You MUST respond with valid JSON only. No markdown, no extra text, no code blocks."
    )


def get_user_prompt(
    topic: str,
    question_count: int,
    difficulty: str,
    category: Optional[str] = None,
    extracted_text: Optional[str] = None,
) -> str:
    source_context = ""
    if extracted_text:
        truncated = extracted_text[:5000] + ("..." if len(extracted_text) > 5000 else "")
        source_context = (
            f"\n\nBase your questions on this document content:\n\n{truncated}"
        )

    category_hint = f" in the category of '{category}'" if category else ""

    diff_guide = {
        "easy": "Basic recall and comprehension questions suitable for beginners.",
        "medium": "Application and analysis questions for intermediate learners.",
        "hard": "Complex reasoning, edge cases, and advanced application questions.",
        "mixed": "A balanced mix of easy (30%), medium (50%), and hard (20%) questions.",
    }.get(difficulty, "Mixed difficulty questions.")

    return (
        f"Generate exactly {question_count} multiple-choice questions about '{topic}'{category_hint}."
        f"{source_context}\n\n"
        f"Difficulty level: {difficulty.upper()} — {diff_guide}\n\n"
        f"Return a JSON object with a single key 'questions' containing an array of {question_count} objects.\n"
        f"Each question object must have:\n"
        f"- question_text: string (the question)\n"
        f"- options: array of exactly 4 strings, each prefixed like 'A. ...', 'B. ...', 'C. ...', 'D. ...'\n"
        f"- correct_option: string, exactly one of 'A', 'B', 'C', or 'D'\n"
        f"- explanation: string (detailed explanation of why the correct answer is right)\n"
        f"- difficulty: string, one of 'easy', 'medium', 'hard'\n"
        f"- category: string (subject category of this question)\n\n"
        f"IMPORTANT: Ensure the correct_option matches one of the options. "
        f"Distractors must be plausible but clearly incorrect to experts."
    )
