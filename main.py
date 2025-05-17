from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from autocorrect_helper.autocorrect_nlp import autocorrect_nlp_text
from regex_helper.regex import process_prompt
from kb_helper.kb_helper import enhance_prompt
from result_helper.result import get_result
from assembly_helper import assemble_prompt

app = FastAPI()
# Point to the templates 
templates = Jinja2Templates(directory="templates")
#Mount the "static" folder 
app.mount("/static", StaticFiles(directory="static"), name="static")
# At the top of your file
prompt_current = ""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html",{
        "request": request,
        "final_optimised_prompt": None
        })

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, initial_prompt: str = Form(...)):
    global prompt_current 
    autocorrect_prompt = autocorrect_nlp_text(initial_prompt)
    regex_prompt = process_prompt(autocorrect_prompt)
    kbtemplate_prompt = enhance_prompt(regex_prompt) # return string
    nlp_enhanced_prompt = ...
    nlp_assembled_prompt = ...
    
    final_optimised_prompt = f"Optimized:, Autocorrect: {autocorrect_prompt},regex_prompt: {regex_prompt}, kbtemplate_prompt: {kbtemplate_prompt}"
    prompt_current = kbtemplate_prompt
    return templates.TemplateResponse("index.html", {
        "request": request,
        "final_optimised_prompt": final_optimised_prompt
    })

@app.get("/result", response_class=HTMLResponse)
async def display_results(request: Request):
    result = get_result(prompt_current)
    return templates.TemplateResponse("result.html",{
        "request": request,
        "final_results": result
    })
