"""
Response Formatter — parses and validates AI JSON responses.
Provides retry signals for malformed responses.
"""
import json
import re
from typing import Any, Optional

from app.core.exceptions import AIProviderError


class ResponseFormatter:
    """
    Parses AI text responses into validated Python objects.
    Handles common AI formatting issues (markdown code fences, extra text,
    unescaped control characters inside string values).
    """

    @staticmethod
    def _sanitize_json_string(text: str) -> str:
        """
        Fix raw control characters (real newlines, tabs, etc.) that appear
        inside JSON string values.  Some LLMs emit literal \\n inside strings
        instead of the JSON-escaped \\\\n, which causes JSONDecodeError with
        "Invalid control character".

        Strategy: scan character by character; inside a JSON string, replace
        bare control chars with their escaped equivalents.
        """
        result = []
        in_string = False
        escaped = False

        for ch in text:
            if escaped:
                result.append(ch)
                escaped = False
                continue

            if ch == '\\' and in_string:
                result.append(ch)
                escaped = True
                continue

            if ch == '"':
                in_string = not in_string
                result.append(ch)
                continue

            if in_string and ord(ch) < 0x20:
                # Replace bare control characters with their JSON escape
                mapping = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}
                result.append(mapping.get(ch, f'\\u{ord(ch):04x}'))
                continue

            result.append(ch)

        return ''.join(result)

    def extract_json(self, raw_text: str) -> dict[str, Any]:
        """
        Extract and parse JSON from AI response text.
        Handles:
        - Pure JSON
        - JSON wrapped in ```json ... ``` or ``` ... ``` code fences
        - JSON prefixed/suffixed with explanatory text
        - Literal newlines / control chars inside JSON string values
        """
        if not raw_text or not raw_text.strip():
            raise AIProviderError("AI returned an empty response")

        text = raw_text.strip()

        def try_parse(s: str) -> dict | None:
            # Try as-is first
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                pass
            # Try with control-char sanitization
            try:
                return json.loads(self._sanitize_json_string(s))
            except json.JSONDecodeError:
                pass
            return None

        # 1. Direct parse
        result = try_parse(text)
        if result is not None:
            return result

        # 2. Strip markdown code fences (```json or ```)
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            inner = fence_match.group(1).strip()
            result = try_parse(inner)
            if result is not None:
                return result

        # 3. Find JSON object boundaries
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            result = try_parse(text[start:end])
            if result is not None:
                return result

        # 4. Find JSON array boundaries (for quiz questions list)
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            result = try_parse(text[start:end])
            if result is not None:
                return {"questions": result}

        raise AIProviderError(
            f"Could not extract valid JSON from AI response. "
            f"Raw text preview: {text[:200]}"
        )

    def validate_summary_response(self, data: dict, sections: list) -> dict[str, str]:
        """Validate summary JSON has all requested sections."""
        result = {}
        for section in sections:
            value = data.get(section, "")
            result[section] = str(value) if value else ""
        return result

    def validate_explanation_response(self, data: dict) -> dict[str, str]:
        """Validate explanation JSON has all required sections."""
        required_sections = [
            "introduction", "step_by_step", "concept_breakdown",
            "real_examples", "analogies", "practical_applications",
            "common_mistakes", "faqs", "final_recap",
        ]
        result = {}
        for section in required_sections:
            result[section] = str(data.get(section, ""))
        return result

    def validate_quiz_response(self, data: dict) -> list[dict]:
        """Validate quiz JSON has the correct structure."""
        questions = data.get("questions", [])

        if not isinstance(questions, list) or len(questions) == 0:
            raise AIProviderError("AI quiz response is missing the 'questions' array")

        validated = []
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                raise AIProviderError(f"Question {i} is not a valid object")

            options = q.get("options", [])
            if not isinstance(options, list) or len(options) != 4:
                raise AIProviderError(f"Question {i} must have exactly 4 options")

            correct = q.get("correct_option", "").upper()
            if correct not in ("A", "B", "C", "D"):
                raise AIProviderError(
                    f"Question {i} has invalid correct_option: '{correct}'"
                )

            validated.append({
                "question_text": str(q.get("question_text", "")),
                "options": [str(o) for o in options],
                "correct_option": correct,
                "explanation": str(q.get("explanation", "")),
                "difficulty": str(q.get("difficulty", "medium")).lower(),
                "category": str(q.get("category", "")) or None,
            })

        return validated


def get_response_formatter() -> ResponseFormatter:
    return ResponseFormatter()
