import re
from typing import Pattern


_PATTERNS: list[tuple[str, Pattern[str]]] = [
    ("heading_atx", re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S")),
    ("heading_setext", re.compile(r"(?ms)^\S.*\n\s*[-=]{3,}\s*$")),
    ("list_bulleted", re.compile(r"(?m)^\s{0,3}[-*+]\s+\S")),
    ("list_numbered", re.compile(r"(?m)^\s{0,3}\d+\.\s+\S")),
    ("blockquote", re.compile(r"(?m)^\s{0,3}>\s+\S")),
    ("code_fence", re.compile(r"(?s)```[\s\S]+?```")),
    ("inline_code", re.compile(r"`[^`]+`")),
    ("link", re.compile(r"\[[^\]]+\]\([^)]+\)")),
    ("image", re.compile(r"!\[[^\]]*\]\([^)]+\)")),
    ("emphasis", re.compile(r"(^|\W)(\*{1,2}|_{1,2}).+?\2(\W|$)")),
    ("table", re.compile(r"(?m)^\s*\|.+\|\s*$")),
]


def is_markdown(text: str) -> bool:
    """Heuristically decide if the given text looks like Markdown.

    Strategy:
    - Count signals from a set of common Markdown patterns.
    - Strong signals (fences, links) can short-circuit.
    - Otherwise require at least 2 distinct signals to reduce false positives.
    """

    if not text or text.isspace():
        return False

    matched_kinds: set[str] = set()
    for kind, pattern in _PATTERNS:
        if pattern.search(text):
            matched_kinds.add(kind)

    if not matched_kinds:
        return False

    # Strong patterns that indicate markdown by themselves
    strong = {"code_fence", "link", "heading_atx", "heading_setext", "emphasis", "inline_code", "list_bulleted", "list_numbered"}
    if matched_kinds & strong:
        return True

    # Otherwise require at least 2 distinct signals
    return len(matched_kinds) >= 2


