# Promptly: A Prompt Optimizer

Promptly turns rough, vague or misspelled prompts into clear, well-structured prompts that get better answers from large language models (LLMs). It runs each prompt through a multi-stage NLP pipeline. Users can then send the optimized prompt to an LLM (Google Gemini) and see the response.

> Built for a hackathon. The idea: the quality of the prompt decides the quality of an AI's answer, so improving the prompt automatically saves users from repeated trial and error.

## Key Features

- **Autocorrect**: fixes spelling with custom fixes, SymSpell and pyspellchecker. When several words are equally close, it uses the surrounding words to choose (*"an esay"* becomes *"an essay"*, but *"its esay"* becomes *"its easy"*), and it flags close calls on the page.
- **Rule-based optimization**: uses regex to expand slang and fix punctuation sentence by sentence, keeping names and acronyms in their original case.
- **Requirements and conflicts**: splits the prompt into a task plus labelled requirements (style, audience, length, scope, timing). It flags contradictions instead of silently dropping one side. Examples: *"not too long"* vs. *"5,000 words"*, *"one sentence"* vs. *"at least 500 words"*, *"use bullet points"* vs. *"don't use bullet points"*, formal vs. casual, experts vs. beginners. You can add new kinds of contradiction as rows in `OPPOSING_REQUIREMENTS`.
- **Knowledge-base template matching**: enriches vague format words (for example *"an essay"* becomes *"a brief essay"*), but only when the prompt sets no length or scope.
- **NLP enhancement**: applies a small curated phrase table (for example *"super technical"* becomes *"highly technical"*). It never swaps content words for synonyms.
- **Grammar assembly**: runs a grammar-only LanguageTool pass that never touches numbers, negations or hyphenated terms, then builds the *Task / Requirements / Conflicting requirements* layout.
- **Requirement safeguard**: after every stage, checks each edit word by word. An edit that would lose a number, a negation or a content word is rejected, the stage's other edits are kept, and the page says what was rejected.
- **Pipeline transparency**: shows the output of every stage next to the final optimized prompt.
- **LLM results**: sends the optimized prompt to Google Gemini and shows the response.

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python, FastAPI, Uvicorn |
| NLP        | LanguageTool (`language_tool_python`), SymSpell, pyspellchecker, Regex |
| Frontend   | Jinja2 templates, HTML, CSS, Bootstrap 5 |
| LLM API    | Google Gemini API (OpenAI-compatible endpoint) |

## How It Works

```
User prompt
   │
   ▼
1. Autocorrect          (autocorrect_helper)
2. Rule-based logic     (regex_helper)   → slang, punctuation, intent, format detection
   Requirements          (requirements_helper) → task, requirements, conflicts
3. KB template match    (kb_helper)      → format enrichment
4. NLP enhancer         (nlp_helper)     → curated phrase table
5. NLP assembler        (assembly_helper)→ safe grammar pass + structured layout
   (pipeline.py checks after every stage that no requirement was lost)
   │
   ▼
Optimized prompt ──► /result → Gemini LLM response (result_helper)
```

## Project Structure

```
Promptly/
├── main.py                  # FastAPI app and routes (/, /result, /info)
├── pipeline.py              # Runs the stages and guards against lost requirements
├── autocorrect_helper/      # Spelling correction + SymSpell frequency dictionary
├── regex_helper/            # Slang dictionary, intent words, format keywords, rule engine
├── requirements_helper/     # Requirement extraction, conflict detection, structured layout
├── kb_helper/               # Knowledge-base format templates
├── nlp_helper/              # Curated phrase table
├── assembly_helper/         # Grammar-only LanguageTool pass
├── result_helper/           # Gemini LLM call
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, logos and images
├── tests/                   # pytest suite
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Runtime + test dependencies
├── Dockerfile
└── .env.example             # Template for your local .env
```

## Running Locally

**Prerequisites:** Python 3.9 or later, and **Java 17 or later**. LanguageTool needs Java, and it downloads its language data the first time it runs.

```bash
git clone https://github.com/kritikarunam30/Promptly.git
cd Promptly

python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt
```

Set your Gemini API key (see [Configuration](#configuration)):

```bash
# macOS / Linux
export GEMINI_API_KEY=your_key_here
# Windows (PowerShell)
$env:GEMINI_API_KEY="your_key_here"
```

Start the server **from the project root**, because the data files are loaded with relative paths:

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000.

> The first start is slow because LanguageTool is downloaded automatically. If Java or LanguageTool isn't available, the grammar pass is skipped and the rest of the pipeline still runs.

### Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests stub out LanguageTool, so they don't need Java. To also run the test that uses the real LanguageTool, set `PROMPTLY_LT_TESTS=1`.

### Using Docker

```bash
docker build -t promptly .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here promptly
# or, with your key in a local .env file:
docker run -p 8000:8000 --env-file .env promptly
```

## Configuration

| Variable             | Required | Description |
|----------------------|----------|-------------|
| `GEMINI_API_KEY` | For `/result` | API key from [Google AI Studio](https://aistudio.google.com/apikey). Without it, the optimizer still works but the LLM results page returns an auth error. |
| `GEMINI_MODEL`       | No       | Gemini model id (default `gemini-2.5-flash`). |
| `PORT`               | No       | Port used by the Docker image (default `8000`). |

Copy `.env.example` to `.env` and fill in your key. `.env` is gitignored and excluded from the Docker image. Never commit real keys.

## Routes

| Method | Path      | Description |
|--------|-----------|-------------|
| GET    | `/`       | Prompt input form |
| POST   | `/`       | Runs the optimization pipeline and shows every stage (prompts up to 4,000 characters) |
| POST   | `/result` | Sends the posted optimized prompt to the LLM and shows the response |
| GET    | `/info`   | About page: vision, how to use and tech stack |
