import re

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
    "default": "clearly and concisely"
}

def enhance_prompt(regex_prompt: dict) -> dict:    
    format_words = regex_prompt["format_words"]
    intent_matches = regex_prompt["intent_words"]
    optimized_prompt = regex_prompt["optimized_prompt"]
    original_prompt = regex_prompt["original_prompt"]
    for fmt in format_words:
        fmt_lower = fmt.lower()
        if fmt_lower in FORMAT_SUGGESTIONS:
            already_specific = re.search(rf"\b{fmt}\s+in\s+\d+\s+\w+", original_prompt, re.IGNORECASE)
            if already_specific:
                return optimized_prompt
            enhanced_format = FORMAT_SUGGESTIONS[fmt_lower]
            pattern = re.compile(r'\b' + re.escape(fmt) + r'\b', re.IGNORECASE)
            optimized_prompt = pattern.sub(enhanced_format, optimized_prompt)
            break

    if not format_words and intent_matches:
        optimized_prompt = optimized_prompt.rstrip(".!?") + f", {FORMAT_SUGGESTIONS['default']}."

    return optimized_prompt