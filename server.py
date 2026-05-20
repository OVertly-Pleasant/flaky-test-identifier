from fastapi import FastAPI
import pandas as pd
from analyzer import connect_n_process

app = FastAPI()

@app.get("/analyse")
def analyse(top: int = 5, show_passrate: bool = False):
    pass_rate = connect_n_process(top,'commits.db')
    output = ["test_name","flakiness"]
    if show_passrate:
        output+=["pass_rate"]
    return pass_rate[output].to_dict(orient='records')

@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/analyse", "/docs"]}