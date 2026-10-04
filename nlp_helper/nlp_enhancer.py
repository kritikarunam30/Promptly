import re

# Curated, meaning-preserving rewrites. Each entry only tightens wording
# (informal intensifier -> standard one, wordy phrase -> shorter one); no entry
# swaps a content word for a "synonym", which is what used to turn
# "unique" into "alone" and "jargon" into "slang".
PHRASE_TABLE = {
    "super technical": "highly technical",
    "super detailed": "highly detailed",
    "super creative": "highly creative",
    "super simple": "very simple",
    "super short": "very short",
    "super long": "very long",
    "super easy": "very easy",
    "super clear": "very clear",
    "in order to": "to",
    "due to the fact that": "because",
    "at this point in time": "now",
}

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(PHRASE_TABLE, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def apply_phrase_table(text):
    """Return (new_text, [(old, new), ...]) for every phrase that was rewritten."""
    changes = []

    def swap(m):
        replacement = PHRASE_TABLE[m.group(0).lower()]
        if m.group(0)[0].isupper():
            replacement = replacement[0].upper() + replacement[1:]
        changes.append((m.group(0), replacement))
        return replacement

    return _PATTERN.sub(swap, text), changes


def nlp_enhancer(kbtemplate_prompt, regex_prompt=None):
    enhanced, _ = apply_phrase_table(kbtemplate_prompt)
    return enhanced
