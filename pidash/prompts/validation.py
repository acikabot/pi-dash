"""Guard rails for prompt edits.

A prompt that loses {transcript} doesn't crash the bot — it cheerfully asks the model to
summarise nothing and sends the result. That silent failure is what this prevents.
"""

from __future__ import annotations


def check_placeholders(text: str, required: tuple[str, ...] | list[str]) -> str | None:
    """Return a complaint, or None when the text is safe to save."""
    if not required:
        return None

    missing = [name for name in required if "{" + name + "}" not in text]
    if missing:
        return "Missing required placeholder(s): " + ", ".join("{" + m + "}" for m in missing)

    try:
        text.format(**dict.fromkeys(required, ""))
    except KeyError as error:
        return f"Unknown placeholder {{{error.args[0]}}}. Available here: " + ", ".join(
            "{" + name + "}" for name in required
        )
    except (ValueError, IndexError):
        return (
            "Unbalanced or malformed braces. Write a literal brace as {{ or }}, and use only "
            + ", ".join("{" + name + "}" for name in required)
        )
    return None
