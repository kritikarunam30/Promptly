import re
from requirements_helper.requirements import has_length_constraint, has_scope_constraint, split_sentences

FORMAT_SUGGESTIONS = {
    "paragraph": "short and crisp paragraph",
    "bullet points": "clear bullet points",
    "bulleted list": "bulleted list with key points",
    "list": "concise list",
    "article": "article in 5 lines",
    "essay": "brief essay",
    "summary": "concise summary",
    "note": "quick note",
    "notes": "important notes",
    "table": "well-organized table",
    "comparison table": "detailed comparison table",
    "timeline": "clear timeline",
    "step-by-step": "step-by-step guide",
    "flowchart": "simple flowchart",
    "code snippet": "clear code snippet",
    "code example": "illustrative code example",
    "script": "concise script",
    "dialogue": "natural dialogue",
    "q&a": "clear Q&A format",
    "question and answer": "clear question and answer section",
    "story": "brief and engaging story",
    "poem": "creative poem",
    "report": "clear and concise report",
    "case study": "detailed case study",
    "infographic": "informative infographic",
    "chart": "clear chart",
    "graph": "insightful graph",
    "presentation": "effective presentation",
    "slide deck": "well-structured slide deck",
    "email": "professional email",
    "letter": "formal letter",
    "tweet": "catchy tweet",
    "thread": "engaging thread",
    "caption": "descriptive caption",
    "captioned image": "captioned image with details",
    "instruction manual": "clear instruction manual",
    "recipe": "detailed recipe",
    "outline": "clear outline",
    "abstract": "concise abstract",
    "blog post": "engaging blog post",
    "newsletter": "informative newsletter",
    "headline": "catchy headline",
    "review": "honest review",
    "explanation": "simple explanation",
    "definition": "clear definition",
    "diagnosis": "thorough diagnosis",
    "plan": "detailed plan",
    "framework": "structured framework",
    "quote": "memorable quote",
    "slogan": "catchy slogan",
    "storyboard": "visual storyboard",
    "transcript": "accurate transcript",
    # Fixed, not random, so the same prompt always gives the same result
    "default": "clearly and concisely"
}

NEGATION_BEFORE = re.compile(r"\b(?:don't|do not|does not|never|no|without|avoid|not)\b(?:\W+\w+){0,3}\W*$", re.IGNORECASE)

def enhance_prompt(regex_prompt: dict) -> str:
    result = regex_prompt
    format_words = result.get("format_words", [])
    intent_matches = result.get("intent_words", [])
    optimized_prompt = result.get("optimized_prompt")
    original_prompt = result.get("original_prompt")

    # A prompt that already sets a length or scope must not get extra size hints such as "briefly"
    if has_length_constraint(original_prompt) or has_scope_constraint(original_prompt):
        return optimized_prompt

    for fmt in format_words:
        fmt_lower = fmt.lower()
        if fmt_lower in FORMAT_SUGGESTIONS:
            # Only enrich a format used as a noun ("an essay", "in a table"), never a verb ("list every...")
            # and never one the user ruled out ("don't use bullet points")
            noun_use = re.search(rf"\b(?:a|an|the|as|in|into)\s+{re.escape(fmt_lower)}\b", optimized_prompt, re.IGNORECASE)
            if not noun_use or NEGATION_BEFORE.search(optimized_prompt[:noun_use.start()]):
                continue

            # Define vague modifier patterns to avoid enhancement if already specific
            patterns = [
                rf"\b\d+[-\s]?\w*\s+{re.escape(fmt_lower)}\b",  # e.g. 300-word article
                rf"\b{re.escape(fmt_lower)}\s+in\s+\d+\s+\w+",  # e.g. article in 10 lines
                rf"\b(?:around|about|in about|approximately|nearly|roughly)\s+\d+\s+\w*\s+{re.escape(fmt_lower)}\b",  # e.g. about 300 word article
                rf"\b{re.escape(fmt_lower)}\s+(?:around|about|approximately|nearly|roughly)\s+\d+\s+\w*",  # e.g. article around 300 words
                rf"\b{re.escape(fmt_lower)}\s+of\s+\d+\s+\w+",  # e.g. summary of 100 words
                rf"\b\d+\s+\w+\s+for\s+(the\s+)?{re.escape(fmt_lower)}\b",  # e.g. 5 lines for the summary
                rf"\b{re.escape(fmt_lower)}\s+(between|from)\s+\d+\s+(and|to)\s+\d+\s+\w+",  # e.g. article from 200 to 300 words
                rf"\b{re.escape(fmt_lower)}\s+(containing|having)\s+\d+\s+\w+",  # e.g. essay containing 100 words
                rf"\b{re.escape(fmt_lower)}\s+in\s+about\s+\d+\s+\w+"

            ]
            already_specific = any(re.search(p, original_prompt, re.IGNORECASE) for p in patterns)

            if already_specific:
                continue  # Skip enhancement

            # Enhance the format
            enhanced_format = FORMAT_SUGGESTIONS[fmt_lower]
            determiner = noun_use.group(0).split()[0]
            if determiner.lower() in ("a", "an"):
                article = "an" if enhanced_format[0].lower() in "aeiou" else "a"
                determiner = article.capitalize() if determiner[0].isupper() else article
            optimized_prompt = (optimized_prompt[:noun_use.start()] + f"{determiner} {enhanced_format}"
                                + optimized_prompt[noun_use.end():])
            break


    if not format_words and intent_matches:
        # Attach the hint to the first (task) sentence, not to whichever sentence happens to be last
        sentences = split_sentences(optimized_prompt)
        if sentences and not sentences[0].endswith("?"):
            sentences[0] = sentences[0].rstrip(".!") + f", {FORMAT_SUGGESTIONS['default']}."
        optimized_prompt = " ".join(sentences)

    return optimized_prompt
