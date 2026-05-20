# 🔍 Flaky Test Identifier

An automated telemetry tool that analyzes CI/CD pipeline history to identify and rank statistically flaky tests. 

## 📖 Overview
Flaky tests are a massive drain on engineering resources. This tool extracts JUnit XML artifact data from GitHub Actions, stores run history locally, and applies statistical variance models to assign a "Flakiness Score" to every test in a repository.

<img width="581" height="142" alt="Screenshot 2026-05-20 at 22 49 55" src="https://github.com/user-attachments/assets/a87f26e7-7c33-4725-baff-21a529c42a83" />

### Architecture
- **Extract & Load:** Custom Python harvester that hits the GitHub REST API, unzips workflow artifacts in memory (`io.BytesIO`), and parses JUnit XML trees into a local SQLite database.
- **Transform:** Pandas-driven analysis engine that groups test history and calculates variance `p * (1-p)`.
- **Presentation:** Decoupled interfaces featuring a Typer/Rich CLI and a FastAPI REST endpoint.

## 🚀 Getting Started

### Prerequisites
1. Python 3.10+
2. A GitHub Personal Access Token (PAT)

### Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/OVertly-Pleasant/flaky-test-identifier.git
cd flaky-test-identifier
pip install -r requirements.txt
```

Create a `.env` file in the root directory and add your GitHub token:
`GITHUB_TOKEN=your_token_here`

## 💻 Usage

**1. Harvest CI/CD Data**
```bash
python harvester.py
```

**2. View in Terminal (CLI)**
```bash
python main.py --top 5 --show-passrate
```

**3. Serve via REST API**
```bash
uvicorn server:app --reload
```
Navigate to `http://localhost:8000/docs` to view the auto-generated Swagger UI.
