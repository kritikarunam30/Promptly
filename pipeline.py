import re
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from autocorrect_helper.autocorrect_nlp import autocorrect_with_report
from regex_helper.regex import process_prompt, normalize_slang, slang_dict
from kb_helper.kb_helper import enhance_prompt
from nlp_helper.nlp_enhancer import nlp_enhancer, apply_phrase_table
from assembly_helper.assembly_nlp import grammar_correct
from requirements_helper.requirements import render_structured, summarize_requirements, extract_requirements

MAX_PROMPT_CHARS = 4000

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "also", "so", "to", "of", "in", "on", "at", "for", "with", "by",
    "it", "its", "is", "are", "be", "this", "that", "these", "those", "as", "if", "then", "than",
    "i", "you", "we", "they", "he", "she", "me", "my", "your", "our", "their", "them", "us",
    "do", "does", "did", "will", "would", "can", "could", "should", "please", "just",
    # Auxiliaries: grammar fixes such as "it have" -> "it has" must not count as a lost word
    "have", "has", "had", "was", "were", "been", "being", "am",
}

NEGATION = re.compile(r"\b(?:not|no|never|without|nor)\b|n't\b", re.IGNORECASE)
NUMBER = re.compile(r"\d[\d,.]*\d|\d")


def _stem(word):
    word = word.lower()
    for suffix, repl in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ing", "")):
        if len(word) > 4 and word.endswith(suffix):
            return word[: -len(suffix)] + repl
    return word


def _protected_tokens(text):
    """Tokens no stage may alter: contractions, hyphenated words, numbers, acronyms."""
    tokens = re.findall(r"[\w'-]+", text)
    return {t.lower() for t in tokens if re.search(r"['\-\d]", t) or (len(t) > 1 and t.isupper())}


def _canonical(text):
    """Apply the pipeline's own sanctioned rewrites (slang, phrase table), so "plz" vs "please" or
    "super technical" vs "highly technical" compare equal, while "super" -> "ace" still counts as a loss."""
    return apply_phrase_table(normalize_slang(text, slang_dict))[0]


def _content_stems(text):
    # Counted, not a set: dropping one "make" must be noticed even if another "make" remains
    return Counter(_stem(w) for w in re.findall(r"[A-Za-z]+", _canonical(text)) if w.lower() not in STOPWORDS)


def missing_requirements(before, after, check_words=True):
    """List what `after` lost compared with `before`. Empty list means nothing was lost."""
    missing = []
    after_numbers = NUMBER.findall(after)
    missing += [f"number {n}" for n in NUMBER.findall(before) if n not in after_numbers]
    missing += [f"'{t}'" for t in sorted(_protected_tokens(before) - _protected_tokens(after))]
    if len(NEGATION.findall(after)) < len(NEGATION.findall(before)):
        missing.append("a negation (not / don't / without)")
    if check_words:
        missing += [f"'{w}'" for w in sorted(_content_stems(before) - _content_stems(after))]
    return missing


@dataclass
class PromptState:
    original: str
    text: str
    stages: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    requirements: dict = field(default_factory=dict)

    def apply(self, name, new_text, check_words=True):
        """Accept a stage's edits one by one, rejecting only the edits that would drop a requirement."""
        merged, rejected = merge_safe_edits(self.text, new_text, check_words)
        for old, new, lost in rejected:
            self.notes.append(f"{name}: rejected '{old}' → '{new}' because it would drop {', '.join(lost)}; "
                              "the stage's other changes were kept.")
        self.text = merged
        self.stages[name] = self.text


def _tokens(text):
    return re.findall(r"\S+|\s+", text)


def merge_safe_edits(before, after, check_words=True):
    """Diff the stage output against its input word by word and keep each edit
    only if, together with the edits already kept, it loses nothing.
    Returns (merged text, [(old, new, lost items), ...])."""
    if not missing_requirements(before, after, check_words):
        return after, []
    a, b = _tokens(before), _tokens(after)
    ops = SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    keep = [tag == "equal" for tag, *_ in ops]

    def build():
        return "".join("".join(b[j1:j2] if keep[k] else a[i1:i2]) for k, (_, i1, i2, j1, j2) in enumerate(ops))

    rejected = []
    for k, (tag, i1, i2, j1, j2) in enumerate(ops):
        if tag == "equal":
            continue
        keep[k] = True
        lost = missing_requirements(before, build(), check_words)
        if lost:
            keep[k] = False
            rejected.append(("".join(a[i1:i2]).strip(), "".join(b[j1:j2]).strip(), lost))
    return build(), rejected


def run_pipeline(initial_prompt, tool=None):
    state = PromptState(original=initial_prompt, text=initial_prompt.strip())

    # Spelling fixes legitimately change words, so only numbers, negations and protected tokens are checked
    corrected, corrections = autocorrect_with_report(state.text)
    state.apply("Autocorrected Prompt", corrected, check_words=False)
    for typo, fix, close in corrections:
        if close:
            state.notes.append(f"Autocorrect: '{typo}' → '{fix}' was a close call "
                               f"(also possible: {', '.join(close)}). Check that this is what you meant.")

    regex_prompt = process_prompt(state.text)
    state.apply("Rule Based Logic", regex_prompt["optimized_prompt"])
    state.requirements = extract_requirements(state.text)
    state.stages["Requirements & Conflicts"] = summarize_requirements(state.text)

    # KB and later stages always receive the complete text accepted so far
    regex_prompt["optimized_prompt"] = state.text
    state.apply("Knowledge-Base Template Matching", enhance_prompt(regex_prompt))
    state.apply("NLP Enhancer Prompt", nlp_enhancer(state.text))
    state.apply("NLP Assembled Prompt", grammar_correct(state.text, tool))

    structured = render_structured(state.text)
    state.apply("Optimized Prompt", structured)
    return state
