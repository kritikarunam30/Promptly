import language_tool_python

class NLPEngine:
    def __init__(self):
        self.language_tool = language_tool_python.LanguageTool('en-US')          

    def language_tool_correction(self, text):
        matches = self.language_tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)
        return corrected_text


def assemble_nlp_text(user_input):    
    if user_input.lower() == 'exit':
        return None
    nlp = NLPEngine()
    return nlp.language_tool_correction(user_input) 

