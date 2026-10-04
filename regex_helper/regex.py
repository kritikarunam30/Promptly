import os
import re
from json import load
from regex_helper.intent_file import intent_words
from regex_helper.format  import content_formats

# Load slang dictionary
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slang_dict.json"), "r") as f:
    slang_dict = load(f)

# Define the prompt type optimizer classes
class PromptOptimizer:
    def optimize(self, text: str) -> str:
        raise NotImplementedError("Subclasses must implement optimize()")

class Question(PromptOptimizer):
    def optimize(self, text: str) -> str:
        return text.rstrip('.!?') + '?'

class Command(PromptOptimizer):
    def optimize(self, text: str) -> str:
        # Keep an existing "!" or "?"; only add a full stop when the sentence has no end mark
        if not re.search(r'[.?!]$', text):
            text += "."
        return text

class Greeting(PromptOptimizer):
    def optimize(self, text: str) -> str:
        parts = text.split()
        if not parts:
            return text

        # Capitalize first word
        parts[0] = parts[0].capitalize()

        # Rebuild sentence; "Good morning" stays together instead of becoming "Good, morning"
        if len(parts) > 1 and parts[0].lower() == "good":
            parts = [parts[0] + ' ' + parts[1]] + parts[2:]
        word = parts[0].rstrip(',!')
        greeting_part = word + ',' if len(parts) > 1 else word + '!'
        rest = ' '.join(parts[1:]) if len(parts) > 1 else ''

        # Add exclamation at the end
        if rest:
            rest = rest.rstrip('.!?') + '!'
            return f"{greeting_part} {rest}"
        else:
            return greeting_part


class QuestionWithGreeting(PromptOptimizer):
    def optimize(self, text: str) -> str:
        return Question().optimize(Greeting().optimize(text))

class CommandWithGreeting(PromptOptimizer):
    def optimize(self, text: str) -> str:
        return Command().optimize(Greeting().optimize(text))

class QuestionWithCommand(PromptOptimizer):
    def optimize(self, text: str) -> str:
        text = text.strip()
        if not text:
            return text

        # Capitalize the first character only, so names and acronyms keep their case
        text = text[0].upper() + text[1:]

        # Ensure it ends with a question mark
        text = text.rstrip(".!?") + "?"
        return text



class NoKnownCategory(PromptOptimizer):
    def optimize(self, text: str) -> str:
        self.text = text.strip()
        if not re.search(r'[.?!]$', self.text):
            self.text += '.'
        return self.text
# Helper functions
def normalize_slang(text, slang_dict):
    pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in slang_dict.keys()) + r')\b', re.IGNORECASE)

    def expand(m):
        replacement = slang_dict[m.group().lower()]
        return replacement[0].upper() + replacement[1:] if m.group()[0].isupper() else replacement
    return pattern.sub(expand, text)

def clean_prompt(sentence):
    clean_word = re.sub(r"\s+", " ", sentence)
    clean_word = re.sub(r'([.,!?])\1+', r'\1', clean_word)
    clean_word = re.sub(r'\s+([.,!?;:])', r'\1', clean_word)
    clean_word = clean_word.strip()
    # Only the first letter changes; str.capitalize() would lowercase "Earth" or "AI"
    return clean_word[:1].upper() + clean_word[1:]


def prompt_type(text):
    text = text.lower()

    scores = {
        "Greeting": 0,
        "Command": 0,
        "Question": 0,
    }

    greeting_keywords = ["hi", "hello", "greetings", "congratulations", "hey", "yo", "good morning", "good evening"]
    command_keywords = ["give", "generate", "make", "do", "please", "will", "get", "go", "create", "write","tell"]
    question_keywords = ["how", "what", "why", "where", "can", "could", "should", "is", "are", "do", "does", "will", "would","explain"]

    for word in greeting_keywords:
        if re.search(rf"\b{re.escape(word)}\b", text):
            scores["Greeting"] += 1

    for word in command_keywords:
        if re.search(rf"\b{re.escape(word)}\b", text):
            scores["Command"] += 1

    for word in question_keywords:
        if re.search(rf"\b{re.escape(word)}\b", text):
            scores["Question"] += 1

    # Determine highest scoring category/categories
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_score = sorted_scores[0][1]
    top_categories = [k for k, v in sorted_scores if v == top_score and v > 0]

    # Handle combinations
    if "Question" in top_categories and "Command" in top_categories:
        return "QuestionWithCommand"
    elif "Question" in top_categories and "Greeting" in top_categories:
        return "QuestionWithGreeting"
    elif "Command" in top_categories and "Greeting" in top_categories:
        return "CommandWithGreeting"
    elif top_categories:
        return top_categories[0]
    else:
        return "None"


GREETINGS = ("hi", "hello", "hey", "greetings", "yo", "good morning", "good evening", "good afternoon")
WH_WORDS = ("how", "what", "why", "where", "when", "who", "whom", "whose", "which")
AUX_WORDS = ("can", "could", "should", "would", "will", "is", "are", "was", "were", "does", "did", "may", "might", "shall", "am")

def sentence_type(sentence):
    """Classify one sentence by its shape rather than by keywords anywhere in it."""
    words = re.findall(r"[\w']+", sentence.lower())
    greeting = False
    for g in GREETINGS:
        g_words = g.split()
        if words[:len(g_words)] == g_words:
            greeting = True
            words = words[len(g_words):]
            break
    first = words[0] if words else ""
    second = words[1] if len(words) > 1 else ""
    question = (
        sentence.rstrip().endswith("?")
        or first in WH_WORDS
        or first in AUX_WORDS
        # "Do you know..." is a question, "Do it now" is a command
        or (first == "do" and second in ("you", "we", "they", "i"))
    )
    if greeting and question:
        return "QuestionWithGreeting"
    if greeting and words:
        return "CommandWithGreeting"
    if greeting:
        return "Greeting"
    if question:
        return "Question"
    return "Command"

# Optimizer router
def get_optimizer_class(prompt_type_str):
    return {
        "Question": Question(),
        "Command": Command(),
        "Greeting": Greeting(),
        "QuestionWithGreeting": QuestionWithGreeting(),
        "CommandWithGreeting": CommandWithGreeting(),
        "QuestionWithCommand": QuestionWithCommand(),
        "None": NoKnownCategory()
    }.get(prompt_type_str, NoKnownCategory())
def capitalize_after_punctuation(text):
    text = text.strip()

    # Capitalize the first character of the string
    if text:
        text = text[0].upper() + text[1:]

    # Capitalize letter after . ! or ? followed by space(s)
    def capitalize_match(match):
        return match.group(1) + ' ' + match.group(2).upper()

    text = re.sub(r'([.!?])\s+([a-z])', capitalize_match, text)
    text = re.sub(r'\b(i)\b', 'I', text)
    return text

def extract_intent_words(L):
    words = re.findall(r'\b\w+\b', L.lower())  # tokenize words
    intent_found = [word for word in words if word in intent_words]
    return {
        "intent_words": intent_found
    }

def extract_format_words(text):
    text = text.lower()
    found_formats = []

    for fmt in content_formats:
        # Escape the format string in case it has special characters
        pattern = r'\b' + re.escape(fmt) + r'\b'
        if re.search(pattern, text):
            found_formats.append(fmt)

    return {
        "format_words": found_formats,
         
    }

def split_sentences(text):
    return [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s]

def process_prompt(sentence: str):
    cleaned_input = clean_prompt(sentence)
    normalized = normalize_slang(sentence, slang_dict)
    cleaned = clean_prompt(normalized)
    ptype = prompt_type(cleaned)
    # Fix end punctuation sentence by sentence so every sentence of the prompt is kept
    optimized = ' '.join(
        get_optimizer_class(sentence_type(s)).optimize(s) for s in split_sentences(cleaned)
    )
    capitalized = capitalize_after_punctuation(optimized)

    return {
        "prompt_type": ptype,
        "optimized_prompt": capitalized,
        "intent_words": extract_intent_words(cleaned_input)["intent_words"],
        "format_words": extract_format_words(cleaned_input)["format_words"],
        "original_prompt": cleaned_input
    }