import re
import random

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
    "default": random.choice(["clearly and concisely", "briefly"])
}
def enhance_prompt(regex_prompt: dict) -> dict:
    result = regex_prompt
    format_words = result.get("format_words", [])
    intent_matches = result.get("intent_words", [])
    optimized_prompt = result.get("optimized_prompt")
    original_prompt = result.get("original_prompt")

    for fmt in format_words:
        fmt_lower = fmt.lower()
        if fmt_lower in FORMAT_SUGGESTIONS:

            # Define vague modifier patterns to avoid enhancement if already specific
            patterns = [
                rf"\b\d+[-\s]?\w*\s+{re.escape(fmt_lower)}\b",  # e.g. 300-word article
                rf"\b{re.escape(fmt_lower)}\s+in\s+\d+\s+\w+",  # e.g. article in 10 lines
                rf"\b(?:around|about|in about|approximately|nearly|roughly)\s+\d+\s+\w*\s+{re.escape(fmt_lower)}\b",  # e.g. about 300 word article
                rf"\b{re.escape(fmt_lower)}\s+(?:around|about|approximately|nearly|roughly)\s+\d+\s+\w*",  # e.g. article around 300 words
                rf"\b{re.escape(fmt_lower)}\s+of\s+\d+\s+\w+",  # e.g. summary of 100 words
                rf"\b\d+\s+\w+\s+for\s+(the\s+)?{re.escape(fmt_lower)}\b",  # e.g. 5 lines for the summary
                rf"\b{re.escape(fmt_lower)}\s+(between|from)\s+\d+\s+(and|to)\s+\d+\s+\w+",  # e.g. article from 200 to 300 words
                rf"\b{re.escape(fmt_lower)}\s+(containing|having)\s+\d+\s+\w+"  # e.g. essay containing 100 words
                rf"\b{re.escape(fmt_lower)}\s+in\s+about\s+\d+\s+\w+"

            ]
            already_specific = any(re.search(p, original_prompt, re.IGNORECASE) for p in patterns)

            if already_specific:
                continue  # Skip enhancement

            # Enhance the format
            enhanced_format = FORMAT_SUGGESTIONS[fmt_lower]
            pattern = re.compile(r'\b' + re.escape(fmt) + r'\b', re.IGNORECASE)
            optimized_prompt = pattern.sub(enhanced_format, optimized_prompt, count=1)
            break


    if not format_words and intent_matches:
        optimized_prompt = optimized_prompt.rstrip(".!?") + f", {FORMAT_SUGGESTIONS['default']}."

    return optimized_prompt
