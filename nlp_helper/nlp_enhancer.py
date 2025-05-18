import re
import nltk
import language_tool_python
from nltk.corpus import wordnet as wn
from kb_helper.kb_helper import FORMAT_SUGGESTIONS

# Download required NLTK resources
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('wordnet')

tool = language_tool_python.LanguageTool('en-US')

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wn.ADJ
    elif treebank_tag.startswith('V'):
        return wn.VERB
    elif treebank_tag.startswith('N'):
        return wn.NOUN
    elif treebank_tag.startswith('R'):
        return wn.ADV
    else:
        return None

def is_simple_word(word):
    """Avoid long or complex synonyms"""
    return word.isalpha() and len(word) <= 10 and '_' not in word

def replace_synonyms(text, preserve_words):
    words = nltk.word_tokenize(text)
    tagged = nltk.pos_tag(words)
    new_words = []

    for word, tag in tagged:
        lower_word = word.lower()
        if lower_word in preserve_words or not word.isalpha():
            new_words.append(word)
            continue

        wn_tag = get_wordnet_pos(tag)
        if wn_tag:
            synsets = wn.synsets(lower_word, pos=wn_tag)
            if synsets:
                lemmas = synsets[0].lemmas()
                for lemma in lemmas:
                    synonym = lemma.name().replace('_', ' ')
                    # Skip long or uncommon synonyms
                    if (
                        synonym.lower() != lower_word
                        and is_simple_word(synonym)
                        and len(synonym) <= len(lower_word) + 2
                    ):
                        new_words.append(synonym if word.islower() else synonym.capitalize())
                        break
                else:
                    new_words.append(word)
            else:
                new_words.append(word)
        else:
            new_words.append(word)

    return ' '.join(new_words)


def nlp_enhancer(kbtemplate_prompt, regex_prompt):
    result = regex_prompt
    optimized_prompt = kbtemplate_prompt
    format_words = result["format_words"]

    preserved_format_terms = set()
    for fmt in format_words:
        fmt_lower = fmt.lower()
        if fmt_lower in FORMAT_SUGGESTIONS:
            suggestion = FORMAT_SUGGESTIONS[fmt_lower]
            optimized_prompt = re.sub(rf"\b{re.escape(fmt)}\b", suggestion, optimized_prompt, flags=re.IGNORECASE)
            preserved_format_terms.update(suggestion.lower().split())

    # Step 1: Replace synonyms but preserve format suggestion terms
    synonym_replaced = replace_synonyms(optimized_prompt, preserved_format_terms)

    # Step 2: Grammar check
    corrected = tool.correct(synonym_replaced)

    return corrected

