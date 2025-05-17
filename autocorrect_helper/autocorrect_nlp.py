import os
from symspellpy.symspellpy import SymSpell, Verbosity
from spellchecker import SpellChecker
from autocorrect_helper.custom_fixes import CUSTOM_FIXES


class NLPEngine:
    def __init__(self):
        self.symspell = SymSpell()
        self.symspell.max_dictionary_edit_distance = 2
        self.symspell.prefix_length = 7

        dict_path = "autocorrect_helper/frequency_dictionary_en_82_765.txt"
        if not os.path.exists(dict_path):
            raise FileNotFoundError(f"SymSpell dictionary file not found: {dict_path}")
        self.symspell.load_dictionary(dict_path, term_index=0, count_index=1)

        self.spellchecker = SpellChecker()


    def apply_custom_fixes(self, text):
        words = text.split()
        fixed_words = []
        for word in words:
            lw = word.lower()
            if lw in CUSTOM_FIXES:
                fixed_word = CUSTOM_FIXES[lw]
                if word[0].isupper():
                    fixed_word = fixed_word.capitalize()
                fixed_words.append(fixed_word)
            else:
                fixed_words.append(word)
        return ' '.join(fixed_words)

    def symspell_correction(self, text):
        suggestions = self.symspell.lookup_compound(text, max_edit_distance=2)
        if suggestions:
            return suggestions[0].term
        return text

    def spellchecker_correction(self, text):
        corrected_words = []
        words = text.split()
        for word in words:
            corrected_word = self.spellchecker.correction(word)
            corrected_words.append(corrected_word)
        return ' '.join(corrected_words)

    def enhance_prompt(self, text):
        text = self.apply_custom_fixes(text)
        text = self.symspell_correction(text)
        text = self.spellchecker_correction(text)        
        return text


def autocorrect_nlp_text(initial_prompt):
    nlp = NLPEngine()
    while True:
        user_input = initial_prompt
        if user_input.lower() == 'exit':
            break
        corrected = nlp.enhance_prompt(user_input)
        return corrected