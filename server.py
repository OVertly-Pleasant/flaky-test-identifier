from fastapi import FastAPI
from analyzer import generate_flakiness_report

app = FastAPI()

@app.get("/analyse")
def analyse(owner: str, repo: str, top: int = 5, show_passrate: bool = False):
    database = f"{owner}_{repo}.db"
    pass_rate = generate_flakiness_report(top,database)
    output = ["test_name","flakiness"]
    if show_passrate:
        output+=["pass_rate"]
    return pass_rate[output].to_dict(orient='records')

@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/analyse", "/docs"]}