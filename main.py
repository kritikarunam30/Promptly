from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from result_helper.result import get_result
from pipeline import run_pipeline, MAX_PROMPT_CHARS

app = FastAPI()
# Point to the templates 
templates = Jinja2Templates(directory="templates")
#Mount the "static" folder 
app.mount("/static", StaticFiles(directory="static"), name="static")

def render_form(request, error=None, initial_prompt=""):
    return templates.TemplateResponse(request, "index.html", {
        "final_optimised_prompt": {},
        "max_chars": MAX_PROMPT_CHARS,
        "error": error,
        "initial_prompt": initial_prompt,
    })

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render_form(request)

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, initial_prompt: str = Form(...)):
    # Reject instead of silently truncating, so no part of the prompt is ever lost
    if not initial_prompt.strip():
        return render_form(request, "Please enter a prompt.")
    if len(initial_prompt) > MAX_PROMPT_CHARS:
        return render_form(request, f"Your prompt is {len(initial_prompt)} characters; the limit is {MAX_PROMPT_CHARS}.", initial_prompt)

    state = run_pipeline(initial_prompt)
    final_optimised_prompt = {"Optimized Prompt": state.text,
                              "Autocorrected Prompt": state.stages["Autocorrected Prompt"],
                              "Rule Based Logic": state.stages["Rule Based Logic"],
                              "Requirements & Conflicts": state.stages["Requirements & Conflicts"],
                              "Knowledge-Base Template Matching": state.stages["Knowledge-Base Template Matching"],
                              "NLP Enhancer Prompt": state.stages["NLP Enhancer Prompt"],
                              "NLP Assembled Prompt": state.stages["NLP Assembled Prompt"]
                            }
    
    return templates.TemplateResponse(request, "index.html", {
        "final_optimised_prompt": final_optimised_prompt,
        "optimized_prompt": state.text,
        "notes": state.notes
    })

# The optimized prompt is posted back from the page, so users never see each other's prompts
@app.post("/result", response_class=HTMLResponse)
async def display_results(request: Request, prompt: str = Form(...)):
    result = get_result(prompt)
    return templates.TemplateResponse(request, "result.html", {
        "final_results": result
    })

@app.get("/result")
async def result_without_prompt():
    return RedirectResponse("/")

@app.get("/info", response_class=HTMLResponse)
async def info(request: Request):
    return templates.TemplateResponse(request, "info.html")
