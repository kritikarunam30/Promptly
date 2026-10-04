import re

# Only fixes that cannot change meaning. TYPOS (spelling) is left to the autocorrect
# stage, and STYLE/REDUNDANCY rules are excluded because they reword the prompt.
ALLOWED_CATEGORIES = {"GRAMMAR", "PUNCTUATION", "CASING", "TYPOGRAPHY"}
ALLOWED_RULES = {"EN_A_VS_AN", "I_LOWERCASE"}

# Spans LanguageTool may never touch: numbers, negations and hyphenated terms
PROTECTED = re.compile(r"\d[\d,.]*|\b\w+n't\b|\b(?:not|no|never|without)\b|\b\w+(?:-\w+)+\b", re.IGNORECASE)

_tool = None
_tool_failed = False

def get_language_tool():
    """One LanguageTool (Java) process for the whole app. Returns None if it cannot start."""
    global _tool, _tool_failed
    if _tool is None and not _tool_failed:
        try:
            import language_tool_python
            _tool = language_tool_python.LanguageTool('en-US')
        except Exception as e:
            print("LanguageTool unavailable, skipping grammar pass:", e)
            _tool_failed = True
    return _tool


def grammar_correct(text, tool=None):
    tool = tool or get_language_tool()
    if tool is None:
        return text
    protected = [m.span() for m in PROTECTED.finditer(text)]
    # Apply from the end so earlier offsets stay valid
    for match in sorted(tool.check(text), key=lambda m: m.offset, reverse=True):
        if match.category not in ALLOWED_CATEGORIES and match.rule_id not in ALLOWED_RULES:
            continue
        if not match.replacements:
            continue
        start, end = match.offset, match.offset + match.error_length
        if any(start < p_end and end > p_start for p_start, p_end in protected):
            continue
        text = text[:start] + match.replacements[0] + text[end:]
    return text
