import os
from re import fullmatch
from symspellpy.symspellpy import SymSpell, Verbosity
from spellchecker import SpellChecker
from autocorrect_helper.custom_fixes import CUSTOM_FIXES

def is_number_like(word):
    return bool(fullmatch(r'\d+(\.\d+)?(st|nd|rd|th)?', word))

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
        fixed_indices = set()

        for i, word in enumerate(words):
            lw = word.lower()
            if lw in CUSTOM_FIXES:
                fixed_word = CUSTOM_FIXES[lw]
                if word[0].isupper():
                    fixed_word = fixed_word.capitalize()
                fixed_words.append(fixed_word)
                fixed_indices.add(i)
            else:
                fixed_words.append(word)
        return fixed_words, fixed_indices
    
    def symspell_correction(self, words, fixed_indices):
        corrected_words = []
        for i, word in enumerate(words):
            if i in fixed_indices or is_number_like(word):
                corrected_words.append(word)
            else:
                suggestions = self.symspell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
                if suggestions:
                    corrected_words.append(suggestions[0].term)
                else:
                    corrected_words.append(word)
        return corrected_words

    def spellchecker_correction(self, words, fixed_indices):
        corrected_words = []
        for i, word in enumerate(words):
            if i in fixed_indices or is_number_like(word):
                corrected_words.append(word)
            else:
                corrected_word = self.spellchecker.correction(word)
                corrected_words.append(corrected_word)
        return corrected_words
    
    def enhance_prompt(self, text):
        words, fixed_indices = self.apply_custom_fixes(text)
        words = self.symspell_correction(words, fixed_indices)
        words = self.spellchecker_correction(words, fixed_indices)
        return ' '.join(words)



def autocorrect_nlp_text(initial_prompt):
    nlp = NLPEngine()
    while True:
        user_input = initial_prompt
        if user_input.lower() == 'exit':
            break
        corrected = nlp.enhance_prompt(user_input)
        return corrected