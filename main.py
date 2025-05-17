from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from autocorrect_helper.autocorrect_nlp import autocorrect_nlp_text
from regex_helper.regex import process_prompt

app = FastAPI()
# Point to the templates 
templates = Jinja2Templates(directory="templates")
#Mount the "static" folder 
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html",{
        "request": request,
        "final_optimised_prompt": None
        })

@app.post("/", response_class=HTMLResponse)
async def handle_form(request: Request, initial_prompt: str = Form(...)):
    autocorrect_prompt = autocorrect_nlp_text(initial_prompt)
    regex_prompt = process_prompt(autocorrect_prompt)
    nlp_enhanced_prompt = ...
    kbtemplate_prompt = ...
    final_optimised_prompt = f"Optimized:, Autocorrect: {autocorrect_prompt}, regex_prompt: {regex_prompt}"
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "final_optimised_prompt": final_optimised_prompt
    })

@app.get("/info", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("info.html",{"request": request})
