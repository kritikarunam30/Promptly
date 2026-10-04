import math
import os
import re
from json import load
from re import fullmatch
from symspellpy.symspellpy import SymSpell, Verbosity
from spellchecker import SpellChecker
from autocorrect_helper.custom_fixes import CUSTOM_FIXES
from regex_helper.format import content_formats
from regex_helper.intent_file import intent_words

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Slang is expanded later by the rule-based stage, so autocorrect must leave it alone
with open(os.path.join(BASE_DIR, "regex_helper", "slang_dict.json"), "r") as f:
    SLANG_WORDS = set(load(f).keys())

# Words people actually use in prompts. Among equally close candidates these win,
# because general web frequency alone turns "esay" into "ebay".
PROMPT_NOUNS = {w for phrase in content_formats for w in phrase.lower().split() if len(w) > 2} | {
    "example", "examples", "explanation", "topic", "words", "sentences", "paragraphs", "points",
    "steps", "language", "audience", "tone", "style", "format",
}
PROMPT_VERBS = {w for phrase in intent_words for w in phrase.lower().split() if len(w) > 2}
# A noun usually follows a determiner; an instruction verb starts a sentence or follows "to"/"please"
DETERMINERS = {"a", "an", "the", "this", "that", "my", "your", "our", "one", "some", "short", "long"}
VERB_SLOTS = {"", "to", "please", "and", "then", "also", "can", "you", "me"}
DOMAIN_BONUS = 4
WEAK_DOMAIN_BONUS = 0.5
TRANSPOSITION_BONUS = 1.5
ARTICLE_PENALTY = 5
# Candidates scoring within this margin of the winner are reported as alternatives
AMBIGUITY_MARGIN = 2

def is_number_like(word):
    return bool(fullmatch(r'\d+(\.\d+)?(st|nd|rd|th)?', word))

def split_token(token):
    """Split 'jargon,' into ('', 'jargon', ',') so punctuation survives correction."""
    m = re.match(r"^(\W*)(.*?)(\W*)$", token)
    return m.group(1), m.group(2), m.group(3)

def match_case(original, corrected):
    if any(c.isupper() for c in corrected):
        return corrected  # e.g. "AI" keeps its own casing
    if original[:1].isupper():
        return corrected[:1].upper() + corrected[1:]
    return corrected

class NLPEngine:
    def __init__(self):
        self.symspell = SymSpell()
        self.symspell.max_dictionary_edit_distance = 2
        self.symspell.prefix_length = 7

        dict_path = os.path.join(BASE_DIR, "autocorrect_helper", "frequency_dictionary_en_82_765.txt")
        if not os.path.exists(dict_path):
            raise FileNotFoundError(f"SymSpell dictionary file not found: {dict_path}")
        self.symspell.load_dictionary(dict_path, term_index=0, count_index=1)

        self.spellchecker = SpellChecker()

    def is_known(self, word):
        lw = word.lower()
        return lw in self.symspell.words or bool(self.spellchecker.known([lw]))

    def should_skip(self, word, sentence_start):
        """Words that must never be 'corrected'."""
        if not word.isalpha():
            return True  # numbers, contractions, hyphenated words, 5,000, five-year-old
        if word.lower() in SLANG_WORDS:
            return True
        if len(word) > 1 and word.isupper():
            return True  # acronyms
        if word[0].isupper() and not sentence_start:
            return True  # proper nouns such as Earth
        return self.is_known(word)

    def score_candidate(self, typo, candidate, count, prev_word):
        """Rank equally close candidates using context instead of raw web frequency alone."""
        score = math.log10(max(count, 1))
        # "an esay" is far more likely "an essay" than "an ebay"; "write a poam" -> "poem"
        if (candidate in PROMPT_NOUNS and prev_word in DETERMINERS) or (candidate in PROMPT_VERBS and prev_word in VERB_SLOTS):
            score += DOMAIN_BONUS
        elif candidate in PROMPT_NOUNS or candidate in PROMPT_VERBS:
            score += WEAK_DOMAIN_BONUS
        if candidate[:1] == typo[:1]:
            score += 1  # people rarely mistype the first letter
        if len(candidate) == len(typo) and sorted(candidate) == sorted(typo):
            score += TRANSPOSITION_BONUS  # "teh" -> "the", "esay" -> "easy" (swapped letters)
        if prev_word in ("a", "an"):
            # "an esay" rules out "say"; "a recipie" rules out vowel-initial words
            if (candidate[:1] in "aeiou") != (prev_word == "an"):
                score -= ARTICLE_PENALTY
        return score

    def correct_word(self, word, prev_word=""):
        """Return (correction, close alternatives); alternatives are listed only when the choice was close."""
        typo = word.lower()
        suggestions = self.symspell.lookup(typo, Verbosity.CLOSEST, max_edit_distance=2)
        if not suggestions:
            corrected = self.spellchecker.correction(typo)
            return (match_case(word, corrected) if corrected else word), []
        ranked = sorted(
            ((self.score_candidate(typo, s.term, s.count, prev_word), s.term) for s in suggestions),
            reverse=True,
        )
        best_score, best = ranked[0]
        close = [term for score, term in ranked[1:] if best_score - score <= AMBIGUITY_MARGIN]
        return match_case(word, best), close

    def correct_text(self, text):
        """Return (corrected text, [(typo, correction, close alternatives), ...])."""
        # Keep whitespace tokens so the original spacing and punctuation are rebuilt exactly
        tokens = re.split(r'(\s+)', text.strip())
        sentence_start = True
        prev_word = ""
        out = []
        corrections = []
        for token in tokens:
            if not token or token.isspace():
                out.append(token)
                continue
            lead, word, trail = split_token(token)
            if word:
                if word.lower() in CUSTOM_FIXES:
                    word = match_case(word, CUSTOM_FIXES[word.lower()])
                elif not is_number_like(word) and not self.should_skip(word, sentence_start):
                    corrected, close = self.correct_word(word, prev_word)
                    if corrected != word:
                        corrections.append((word, corrected, close))
                    word = corrected
            out.append(lead + word + trail)
            prev_word = word.lower() if not trail else ""
            sentence_start = bool(re.search(r'[.!?]$', trail))
        return ''.join(out), corrections

    def enhance_prompt(self, text):
        return self.correct_text(text)[0]


_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = NLPEngine()
    return _engine

def autocorrect_nlp_text(initial_prompt):
    return get_engine().enhance_prompt(initial_prompt)

def autocorrect_with_report(initial_prompt):
    return get_engine().correct_text(initial_prompt)
