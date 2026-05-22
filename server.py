from fastapi import FastAPI
from analyzer import generate_flakiness_report

app = FastAPI()

@app.get("/analyse")
def analyse(owner: str, repo: str, top: int = 5):
    database = f"{owner}_{repo}.db"
    report = generate_flakiness_report(top, database)
    
    if report.empty:
        return {"error": f"No data found for {owner}/{repo}"}
        
    return report.to_dict(orient='records')

@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/analyse", "/docs"]}