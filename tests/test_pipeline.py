import os
import re
from types import SimpleNamespace

import pytest

from autocorrect_helper.autocorrect_nlp import autocorrect_nlp_text
from assembly_helper.assembly_nlp import grammar_correct
from kb_helper.kb_helper import enhance_prompt
from nlp_helper.nlp_enhancer import nlp_enhancer
from pipeline import PromptState, missing_requirements, run_pipeline
from regex_helper.regex import process_prompt
from requirements_helper.requirements import CONFLICT_HEADER, detect_conflicts

EXAMPLE = (
    "Write something really creative and unique about animals. Make it super technical and use deep "
    "scientific jargon, but also use very simple language that a five-year-old can understand. Don't make "
    "it too long, but make sure it has 5,000 words and covers every single species that ever lived on "
    "Earth without leaving anything out. Do it now."
)

EXAMPLE_REQUIREMENTS = [
    "creative", "unique", "animals", "technical", "deep scientific jargon", "very simple language",
    "five-year-old can understand", "Don't make it too long", "5,000 words", "every single species",
    "ever lived on Earth", "without leaving anything out", "Do it now",
]


@pytest.fixture(scope="module")
def example_state():
    return run_pipeline(EXAMPLE)


# ---------- The exact example prompt ----------

def test_example_final_prompt_keeps_every_requirement(example_state):
    for phrase in EXAMPLE_REQUIREMENTS:
        assert phrase in example_state.text, phrase


def test_example_has_no_corrupted_words(example_state):
    final = example_state.text
    for bad in ["alone", "slang", "won't", "will not", "briefly", "to it now", "screen", "dwell"]:
        assert not re.search(rf"\b{re.escape(bad)}\b", final, re.IGNORECASE), bad
    assert "earth" not in final  # proper noun keeps its capital


def test_every_stage_carries_the_complete_prompt(example_state):
    for name, text in example_state.stages.items():
        for phrase in ["5,000 words", "five-year-old", "Earth", "Do it now", "Don't make it too long"]:
            assert phrase in text, f"{name} lost {phrase!r}"
    assert example_state.notes == []


def test_example_is_structured(example_state):
    lines = example_state.text.splitlines()
    assert lines[0] == "Task: Write something really creative and unique about animals."
    assert "Requirements:" in lines
    assert "- Length: Don't make it too long." in lines
    assert "- Timing: Do it now." in lines
    assert CONFLICT_HEADER in lines


def test_example_reports_all_three_conflicts(example_state):
    conflicts = example_state.text.split(CONFLICT_HEADER)[1]
    assert "Technical depth vs. audience" in conflicts and "five-year-old" in conflicts
    assert '"Don\'t make it too long" vs. "5,000 words"' in conflicts
    assert "Scope vs. length" in conflicts and "every single species" in conflicts


def test_only_phrase_table_rewrites_wording(example_state):
    assert "highly technical" in example_state.text
    assert "super technical" not in example_state.text


def test_output_is_deterministic():
    assert run_pipeline(EXAMPLE).text == run_pipeline(EXAMPLE).text


# ---------- Individual stages on the example ----------

def test_autocorrect_leaves_correct_text_untouched():
    assert autocorrect_nlp_text(EXAMPLE) == EXAMPLE


def test_autocorrect_still_fixes_real_typos():
    assert autocorrect_nlp_text("writting an essay about teh enviroment") == "writing an essay about the environment"
    assert autocorrect_nlp_text("explain ai plz") == "explain AI please"


@pytest.mark.parametrize("typo, expected", [
    ("writting an esay about teh enviroment", "writing an essay about the environment"),  # noun after "an"
    ("its esay to lern", "its easy to learn"),  # swapped letters, no determiner
    ("give me a recipie for cake", "give me a recipe for cake"),
    ("wrte a poam about the sea", "write a poem about the sea"),
    ("genrate a tabel of results", "generate a table of results"),
    ("make a lsit of fruits", "make a list of fruits"),
])
def test_autocorrect_uses_context_for_ambiguous_typos(typo, expected):
    assert autocorrect_nlp_text(typo) == expected


def test_close_call_corrections_are_reported():
    state = run_pipeline("describe animals that live in teh ocen")
    assert any("'ocen'" in n and "ocean" in n for n in state.notes)


def test_rule_based_keeps_all_sentences_and_casing():
    out = process_prompt(EXAMPLE)["optimized_prompt"]
    assert out == EXAMPLE
    assert process_prompt("Do it now")["optimized_prompt"] == "Do it now."  # a command, not a question


def test_kb_adds_no_size_hint_when_length_is_given():
    regex_prompt = process_prompt(EXAMPLE)
    assert enhance_prompt(regex_prompt) == regex_prompt["optimized_prompt"]


def test_kb_does_not_treat_verb_list_as_format():
    out = enhance_prompt(process_prompt("list the planets of the solar system"))
    assert "concise list" not in out


def test_phrase_table_never_swaps_content_words():
    text = "Write something unique using deep scientific jargon and super simple words."
    assert nlp_enhancer(text) == "Write something unique using deep scientific jargon and very simple words."


# ---------- Edge cases ----------

def test_negation_is_preserved():
    assert run_pipeline("Don't use bullet points").text == "Don't use bullet points."
    assert run_pipeline("dont use bullet points").text == "Don't use bullet points."


def test_numeric_length_contradiction_is_flagged():
    state = run_pipeline("Write a 300-word essay but keep it under 100 words")
    assert state.text.startswith("Task: Write a 300-word essay.")
    assert "- Length: Keep it under 100 words." in state.text
    assert '"300-word" vs. "100 words"' in state.text


def test_vague_short_vs_large_minimum_is_flagged():
    assert any("Length" in c for c in detect_conflicts("Write a short story. It must be at least 3,000 words."))


def test_jargon_for_children_is_flagged():
    assert any("audience" in c for c in detect_conflicts("Explain quantum computing to kids using technical jargon."))


@pytest.mark.parametrize("prompt, label", [
    ("Use bullet points to summarize the article. Do not use bullet points.", "Include vs. exclude"),
    ("Include code examples, but avoid examples.", "Include vs. exclude"),
    ("Write a formal email in a casual, conversational tone.", "Tone"),
    ("Write a serious eulogy full of jokes.", "Tone"),
    ("Give an objective, persuasive essay.", "Stance"),
    ("Explain it for experts and beginners with no prior knowledge.", "Audience"),
    ("Answer in one sentence. Write at least 500 words.", "Length"),
    ("Write it in a single paragraph using bullet points.", "Format"),
    ("Write a story in first person and third person.", "Perspective"),
])
def test_other_contradictions_are_flagged(prompt, label):
    assert any(c.startswith(label) for c in detect_conflicts(prompt)), detect_conflicts(prompt)


@pytest.mark.parametrize("prompt", [
    "Write a detailed 2,000-word report on solar energy for engineers.",
    "Explain AI to a 5 year old in 3 bullet points.",
    "Write a 300-word essay with a 50-word summary.",
    "Explain AI to kids. Avoid jargon.",
    "Write in a formal tone, not casual.",
    "Use simple words and avoid technical terms.",
    "Write 3 paragraphs, around 300 words.",
    "Use examples but do not use code.",
    "Write a short poem about the sea.",
])
def test_consistent_requirements_are_not_flagged(prompt):
    assert detect_conflicts(prompt) == []


def test_slang_and_constraints_survive_together():
    out = run_pipeline("explain ai to a 5 year old in 3 bullet pts plz").text
    assert out.startswith("Explain AI to a 5 year old in 3 bullet points please")


def test_names_and_numbers_are_untouched():
    assert run_pipeline("Explain the iPhone 15 Pro's A17 chip").text.startswith("Explain the iPhone 15 Pro's A17 chip")


def test_ambiguous_slang_is_not_expanded():
    assert run_pipeline("how do i reset my user id").text == "How do I reset my user id?"


def test_long_prompt_is_not_truncated():
    prompt = " ".join(["Include the history of the Roman Empire in detail."] * 10)
    assert len(prompt) > 150
    state = run_pipeline(prompt)
    assert state.text.count("Roman Empire") == 10


# ---------- Safeguard ----------

def test_guard_detects_lost_requirements():
    lost = missing_requirements(EXAMPLE, EXAMPLE.replace("Don't", "Do").replace("5,000", "500"))
    assert any("negation" in item for item in lost)
    assert "number 5,000" in lost


def test_guard_rejects_old_synonym_output():
    old_output = ("Write something truly creative and alone about animal do it ace proficient and use deep "
                  "scientific slang but too apply really simple language that a five-year-old can understand")
    state = PromptState(original=EXAMPLE, text=EXAMPLE)
    state.apply("NLP Enhancer Prompt", old_output)
    for phrase in ["unique", "jargon", "super technical", "5,000 words", "Don't make it too long", "Do it now"]:
        assert phrase in state.text, phrase
    assert any("'unique'" in n for n in state.notes) and any("'jargon'" in n for n in state.notes)


def test_guard_keeps_good_edits_and_rejects_only_bad_ones():
    before = "Write a unique story, it have 500 words. dont use jargon"
    stage_output = "Write an alone story; it has 500 words. Don't use slang."
    state = PromptState(original=before, text=before)
    state.apply("Grammar", stage_output)
    # Good fixes kept
    assert "it has 500 words." in state.text
    assert "Don't use" in state.text
    # Bad synonym swaps rejected individually
    assert "unique" in state.text and "alone" not in state.text
    assert "jargon" in state.text and "slang" not in state.text
    assert len(state.notes) == 2 and all("other changes were kept" in n for n in state.notes)


def test_grammar_pass_only_applies_safe_rules():
    text = "I has 5,000 words. Don't make it too long."
    matches = [
        SimpleNamespace(rule_id="BASE_FORM", category="GRAMMAR", offset=2, error_length=3, replacements=["have"]),
        SimpleNamespace(rule_id="X", category="GRAMMAR", offset=6, error_length=5, replacements=["5000"]),
        SimpleNamespace(rule_id="WORDINESS", category="STYLE", offset=33, error_length=8, replacements=["short"]),
        SimpleNamespace(rule_id="Y", category="GRAMMAR", offset=19, error_length=5, replacements=["Do"]),
    ]
    tool = SimpleNamespace(check=lambda t: matches)
    assert grammar_correct(text, tool) == "I have 5,000 words. Don't make it too long."


# ---------- Web app ----------

def test_form_accepts_long_prompt_and_shows_structure(monkeypatch):
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app)
    html = client.post("/", data={"initial_prompt": EXAMPLE}).text
    assert "every single species that ever lived on Earth without leaving anything out" in html
    assert "Conflicting requirements" in html
    assert 'maxlength="150"' not in client.get("/").text


def test_result_uses_posted_prompt(monkeypatch):
    from fastapi.testclient import TestClient
    import main
    monkeypatch.setattr(main, "get_result", lambda prompt: f"LLM saw: {prompt}")
    client = TestClient(main.app)
    assert "LLM saw: Task: hello" in client.post("/result", data={"prompt": "Task: hello"}).text


def test_templates_use_current_starlette_api():
    import warnings
    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app)
    with warnings.catch_warnings():
        warnings.filterwarnings("error", module="starlette.templating")
        for path in ["/", "/info"]:
            assert client.get(path).status_code == 200
        assert client.post("/", data={"initial_prompt": "write an essay"}).status_code == 200


def test_over_limit_prompt_is_rejected_not_truncated():
    from fastapi.testclient import TestClient
    import main
    html = TestClient(main.app).post("/", data={"initial_prompt": "a" * 5000}).text
    assert "the limit is 4000" in html


# ---------- Optional: real LanguageTool ----------

@pytest.mark.languagetool
@pytest.mark.skipif(not os.environ.get("PROMPTLY_LT_TESTS"), reason="set PROMPTLY_LT_TESTS=1 to run")
def test_example_with_real_language_tool():
    state = run_pipeline(EXAMPLE)
    for phrase in EXAMPLE_REQUIREMENTS:
        assert phrase in state.text, phrase
    assert state.notes == []
