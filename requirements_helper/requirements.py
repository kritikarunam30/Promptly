import re

# Order in which requirement categories are listed in a label
CATEGORY_PATTERNS = {
    "Format": r"\b(?:bullet(?:ed)? (?:points?|list)|bullets?|table|json|markdown|numbered list|list|paragraphs?|essay|article|poem|story|email|letter|tweet|outline|summary|report|code)\b",
    "Style": r"\b(?:technical|jargon|formal|informal|casual|friendly|professional|tone|style|creative|funny|humorous|academic|scientific|persuasive|engaging|serious|playful|unique)\b",
    "Audience": r"\b(?:\w+[- ]year[- ]olds?|kids?|child(?:ren)?|beginners?|experts?|audience|students?|layman|laymen|non-technical|simple (?:language|terms|words)|easy to understand|understand|readers?|eli5)\b",
    "Length": r"\b(?:\d[\d,]*\s*-?\s*(?:words?|lines?|sentences?|paragraphs?|pages?|characters?)|short|shorter|brief|briefly|concise|long|lengthy|detailed|in[- ]depth)\b",
    "Scope": r"\b(?:every|all|entire|complete|comprehensive|exhaustive|everything|without leaving anything out|covers?|covering|include|including|only|focus on)\b",
    "Timing": r"\b(?:now|immediately|asap|right away|today|urgent(?:ly)?|quickly)\b",
}

LENGTH_UNITS = r"words?|lines?|sentences?|paragraphs?|pages?|characters?"
NUMBER_WORDS = {
    "one": 1, "single": 1, "a single": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "fifty": 50, "hundred": 100, "a hundred": 100, "one hundred": 100, "thousand": 1000, "a thousand": 1000,
}
_NUMBER = r"\d[\d,]*|" + "|".join(sorted((re.escape(w) for w in NUMBER_WORDS), key=len, reverse=True))
NUMERIC_LENGTH = re.compile(rf"\b({_NUMBER})\s*-?\s*({LENGTH_UNITS})\b", re.IGNORECASE)
# Rough size of each unit in words, so "one sentence" can be compared with "500 words"
WORDS_PER_UNIT = {"word": 1, "sentence": 20, "line": 12, "paragraph": 120, "page": 500, "character": 0.2}
# A different unit is only an estimate, so it must be off by this factor to count as a conflict
CROSS_UNIT_SLACK = 3
# "300-word essay with a 50-word summary" has two legitimate targets
SUB_PART = re.compile(r"\b(?:each|per|every|summary|intro(?:duction)?|conclusion|title|abstract|section|chapter|part)\b", re.IGNORECASE)
MAX_CUES = re.compile(r"\b(?:under|below|less than|fewer than|at most|no more than|not more than|max(?:imum)?(?: of)?|up to|within|limit(?:ed)? to)\s*$", re.IGNORECASE)
MIN_CUES = re.compile(r"\b(?:at least|minimum(?: of)?|more than|over|no less than|no fewer than)\s*$", re.IGNORECASE)

VAGUE_SHORT = re.compile(r"\b(?:(?:don't|do not|doesn't|does not|shouldn't|should not|not)(?:\s+\w+){0,3}?\s+(?:too|very|overly|that) long|short|brief|briefly|concise(?:ly)?|succinct)\b", re.IGNORECASE)
VAGUE_LONG = re.compile(r"\b(?:detailed|lengthy|in[- ]depth|very long|long-form|comprehensive)\b", re.IGNORECASE)

# Thresholds above which a numeric target can no longer be called "short"
LONG_THRESHOLDS = {"word": 1000, "line": 100, "sentence": 50, "paragraph": 10, "page": 5, "character": 6000}
SHORT_THRESHOLDS = {"word": 150, "line": 5, "sentence": 5, "paragraph": 1, "page": 1, "character": 1000}

TECHNICAL = re.compile(r"\b(?:(?:very|super|highly|really|extremely|deeply|quite|heavily)\s+)?technical\b|\b(?:(?:deep|heavy|advanced|complex|scientific|technical)\s+){0,2}jargon\b|\bexpert[- ]level\b|\badvanced terminology\b", re.IGNORECASE)
SIMPLE_AUDIENCE = re.compile(r"\b(?:(?:very|super|really|extremely)\s+)?simple (?:language|terms|words)\b|\b\w+[- ]year[- ]olds?\b|\b(?:kids?|child(?:ren)?|toddlers?|layman|laymen|beginners?|non-technical|eli5)\b|\beasy to understand\b", re.IGNORECASE)
EXHAUSTIVE = re.compile(r"\bevery single \w+|\beach and every \w+|\bwithout (?:leaving anything out|missing anything|exception)\b|\beverything\b|\bexhaustive\b|\b(?:every|all) \w+ (?:that|who) ever \w+|\bcomplete list\b", re.IGNORECASE)

NEGATED_BEFORE = re.compile(r"\b(?:not|no|don't|do not|never|avoid|without)\s+(?:\w+\s+){0,2}$", re.IGNORECASE)

# Requirements that pull in opposite directions. Add a row to cover a new kind of contradiction.
OPPOSING_REQUIREMENTS = [
    ("Tone", r"\bformal\b|\bacademic\b|\bprofessional tone\b", r"\binformal\b|\bcasual\b|\bconversational\b|\bslang\b"),
    ("Tone", r"\bserious\b|\bsolemn\b", r"\bfunny\b|\bhumorous\b|\bjokes?\b|\bplayful\b|\bsilly\b"),
    ("Stance", r"\bobjective\b|\bneutral\b|\bunbiased\b|\bbalanced\b", r"\bpersuasive\b|\bopinionated\b|\bbiased\b|\bone-sided\b"),
    ("Mood", r"\boptimistic\b|\bupbeat\b|\bcheerful\b", r"\bpessimistic\b|\bgloomy\b|\bbleak\b"),
    ("Audience", r"\bexperts?\b|\bspecialists?\b|\badvanced (?:readers|users|audience)\b",
     r"\bbeginners?\b|\bnovices?\b|\bnewcomers?\b|\bno prior knowledge\b"),
    ("Perspective", r"\bfirst[- ]person\b", r"\bthird[- ]person\b"),
    ("Tense", r"\bpast tense\b", r"\bpresent tense\b|\bfuture tense\b"),
    ("Format", r"\bbullet(?:ed)? (?:points?|list)\b|\bnumbered list\b",
     r"\bprose\b|\bplain paragraphs?\b|\bsingle paragraph\b|\bno lists?\b"),
]

# "use/include X" in one place and "don't use / avoid / no X" in another
POSITIVE_DIRECTIVE = re.compile(r"\b(?:use|include|add|mention|show|give|provide|cite)\s+((?:[\w-]+\s+){0,2}[\w-]+)", re.IGNORECASE)
NEGATIVE_DIRECTIVE = re.compile(
    r"\b(?:don't|do not|never|avoid|without|no|exclude|skip|omit)\s+"
    r"(?:(?:use|using|include|including|add|adding|mention|mentioning|show|showing|give|giving|provide|providing|cite|citing)\s+)?"
    r"((?:[\w-]+\s+){0,2}[\w-]+)", re.IGNORECASE)
GENERIC_WORDS = {"a", "an", "the", "any", "some", "it", "its", "them", "this", "that", "of", "to", "and", "or",
                 "in", "on", "for", "with", "make", "more", "too", "very", "your", "my", "be"}

CLAUSE_SPLIT = re.compile(r"\s*;\s*|,?\s+but\s+(?=\w)", re.IGNORECASE)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text):
    return [s for s in SENTENCE_SPLIT.split(text.strip()) if s]


def _tidy_clause(clause, terminal):
    clause = clause.strip().rstrip(".!?,;").strip()
    if not clause:
        return ""
    return clause[0].upper() + clause[1:] + terminal


def split_clauses(text):
    """Split text into sentence-level clauses, breaking on 'but' and ';'.
    Clause wording is kept verbatim; only the first letter and the end mark change."""
    clauses = []
    for sentence in split_sentences(text):
        terminal = "?" if sentence.rstrip().endswith("?") else "."
        parts = [p for p in CLAUSE_SPLIT.split(sentence) if p and p.strip()]
        for i, part in enumerate(parts):
            tidy = _tidy_clause(part, terminal if i == len(parts) - 1 else ".")
            if tidy:
                clauses.append(tidy)
    return clauses


def classify_clause(clause):
    return [name for name, pattern in CATEGORY_PATTERNS.items() if re.search(pattern, clause, re.IGNORECASE)]


def _unit(unit):
    return unit.lower().rstrip("s")


def numeric_lengths(text):
    """Return (value, unit, kind, phrase) for every numeric length; kind is max, min or target."""
    found = []
    for m in NUMERIC_LENGTH.finditer(text):
        number = m.group(1).lower()
        value = NUMBER_WORDS[number] if number in NUMBER_WORDS else int(number.replace(",", ""))
        before = text[max(0, m.start() - 25):m.start()]
        kind = "max" if MAX_CUES.search(before) else "min" if MIN_CUES.search(before) else "target"
        found.append((value, _unit(m.group(2)), kind, m.group(0)))
    return found


def has_length_constraint(text):
    return bool(NUMERIC_LENGTH.search(text) or VAGUE_SHORT.search(text) or VAGUE_LONG.search(text))


def has_scope_constraint(text):
    return bool(EXHAUSTIVE.search(text))


def _quote(phrases):
    seen = []
    for p in phrases:
        if p.lower() not in [s.lower() for s in seen]:
            seen.append(p)
    return ", ".join(f'"{p}"' for p in seen)


def detect_conflicts(text):
    """Find requirements that cannot all be satisfied as written."""
    conflicts = []

    technical = _affirmed(TECHNICAL.pattern, text)
    simple = _affirmed(SIMPLE_AUDIENCE.pattern, text)
    if technical and simple:
        conflicts.append(f"Technical depth vs. audience: {_quote(technical)} vs. {_quote(simple)}.")

    lengths = numeric_lengths(text)
    short = [m.group(0) for m in VAGUE_SHORT.finditer(text)]
    long_ = [m.group(0) for m in VAGUE_LONG.finditer(text)]
    length_conflicts = []
    for value, unit, kind, phrase in lengths:
        if kind in ("target", "min") and short and value >= LONG_THRESHOLDS.get(unit, float("inf")):
            length_conflicts.append((short, [phrase]))
        if kind in ("target", "max") and long_ and value <= SHORT_THRESHOLDS.get(unit, 0):
            length_conflicts.append((long_, [phrase]))
    has_sub_parts = bool(SUB_PART.search(text))
    for v1, u1, k1, p1 in lengths:
        for v2, u2, k2, p2 in lengths:
            if u1 == u2:
                too_big = v2 > v1
            else:
                too_big = v2 * WORDS_PER_UNIT[u2] > v1 * WORDS_PER_UNIT[u1] * CROSS_UNIT_SLACK
            if k1 == "max" and k2 in ("target", "min") and too_big:
                length_conflicts.append(([p2], [p1]))
            elif k1 == "target" and k2 == "min" and too_big:
                length_conflicts.append(([p1], [p2]))
            elif k1 == "target" and k2 == "target" and too_big and not has_sub_parts:
                length_conflicts.append(([p1], [p2]))
    for left, right in length_conflicts:
        line = f"Length: {_quote(left)} vs. {_quote(right)}."
        if line not in conflicts:
            conflicts.append(line)

    exhaustive = [m.group(0) for m in EXHAUSTIVE.finditer(text)]
    limits = short + [p for _, _, kind, p in lengths if kind in ("target", "max")]
    if exhaustive and limits:
        conflicts.append(
            f"Scope vs. length: {_quote(exhaustive)} vs. a length limit ({_quote(limits)}); "
            "complete coverage may not fit, so state what is prioritized or left out."
        )

    for label, side_a, side_b in OPPOSING_REQUIREMENTS:
        found_a, found_b = _affirmed(side_a, text), _affirmed(side_b, text)
        if found_a and found_b:
            conflicts.append(f"{label}: {_quote(found_a)} vs. {_quote(found_b)}.")

    conflicts += _include_exclude_conflicts(text)
    return conflicts


def _affirmed(pattern, text):
    """Matches of pattern that are not negated ("not formal" does not ask for formality)."""
    return [m.group(0) for m in re.finditer(pattern, text, re.IGNORECASE)
            if not NEGATED_BEFORE.search(text[max(0, m.start() - 30):m.start()])]


def _object_words(phrase):
    return {w.lower().rstrip("s") for w in re.findall(r"[\w-]+", phrase) if w.lower() not in GENERIC_WORDS}


def _trim(phrase):
    """Drop trailing filler such as "to" from a quoted phrase: "Use bullet points to" -> "Use bullet points"."""
    words = phrase.split()
    while len(words) > 2 and words[-1].lower() in GENERIC_WORDS:
        words.pop()
    return " ".join(words)


def _include_exclude_conflicts(text):
    negatives = [(_trim(m.group(0)), _object_words(m.group(1))) for m in NEGATIVE_DIRECTIVE.finditer(text)]
    conflicts = []
    for m in POSITIVE_DIRECTIVE.finditer(text):
        if NEGATED_BEFORE.search(text[max(0, m.start() - 30):m.start()]):
            continue  # this is the "don't use X" itself
        wanted = _object_words(m.group(1))
        for phrase, unwanted in negatives:
            if wanted & unwanted:
                line = f'Include vs. exclude: "{_trim(m.group(0))}" vs. "{phrase}".'
                if line not in conflicts:
                    conflicts.append(line)
    return conflicts


def extract_requirements(text):
    """Return the task clause, the labelled requirement clauses and any conflicts."""
    clauses = split_clauses(text)
    if not clauses:
        return {"task": "", "requirements": [], "conflicts": []}
    requirements = []
    for clause in clauses[1:]:
        labels = classify_clause(clause) or ["Instruction"]
        requirements.append({"labels": labels, "text": clause})
    return {"task": clauses[0], "requirements": requirements, "conflicts": detect_conflicts(text)}


CONFLICT_HEADER = ("Conflicting requirements (do not silently drop either side; "
                   "explain in your response how you balance or resolve each one):")


def render_structured(text):
    """Lay the prompt out as Task / Requirements / Conflicting requirements.
    A prompt with a single clause and no conflicts is returned unchanged."""
    extracted = extract_requirements(text)
    if not extracted["requirements"] and not extracted["conflicts"]:
        return text.strip()
    lines = [f"Task: {extracted['task']}"]
    if extracted["requirements"]:
        lines.append("Requirements:")
        lines += [f"- {', '.join(r['labels'])}: {r['text']}" for r in extracted["requirements"]]
    if extracted["conflicts"]:
        lines.append(CONFLICT_HEADER)
        lines += [f"- {c}" for c in extracted["conflicts"]]
    return "\n".join(lines)


def summarize_requirements(text):
    """One-line-per-item summary shown as a pipeline stage."""
    extracted = extract_requirements(text)
    parts = [f"Task: {extracted['task']}"]
    parts += [f"{', '.join(r['labels'])}: {r['text']}" for r in extracted["requirements"]]
    parts += [f"Conflict: {c}" for c in extracted["conflicts"]] or ["Conflicts: none detected"]
    return " | ".join(parts)
