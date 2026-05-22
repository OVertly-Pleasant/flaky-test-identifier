# 🔍 Flaky Test Identifier

An automated telemetry tool that analyzes CI/CD pipeline history to identify and rank statistically flaky tests using multi-dimensional time-series analysis.

## 📖 Overview
Flaky tests are a massive drain on engineering resources. Simple pass/fail variance is often misleading, falling victim to false positives like permanently broken code or low-run insignificance. 

This tool extracts JUnit XML artifact data from GitHub Actions, stores run history locally, and passes the data through a modular "Pipeline of Evaluators." Instead of simple variance, it calculates chronological flip rates, execution time anomalies, and time-of-day clustering to assign an "Ultimate Chaos Score" to every test.

<img width="739" height="172" alt="Screenshot 2026-05-22 at 22 01 46" src="https://github.com/user-attachments/assets/b9267a54-52f7-47dd-9adf-5e35603f6c50" />

## 🧠 Analysis Modules
- **Statistical Significance Filter:** Automatically ignores tests with `< 5` runs to prevent "Law of Small Numbers" false positives.
- **Flip Rate:** Chronological transition counting to detect true status flip-flops (Pass $\rightarrow$ Fail $\rightarrow$ Pass) to ignore standard regressions.
- **Duration Anomaly:** Analyzes the execution time delta between passed and failed runs to detect resource starvation, timeouts, and database locks.
- **Time Anomaly:** Extracts ISO timestamps to detect if failures cluster around specific hours of the day (e.g., UTC timezone bugs or high-traffic periods).

## 🏗️ Architecture
- **Extract & Load:** Custom Python Harvester that interacts with the GitHub REST API, unzips workflow artifacts in memory (`io.BytesIO`), and parses JUnit XML trees into a dynamic SQLite database (`owner_repo.db`).
- **Defensive Design:** Implements idempotency to prevent duplicate artifact ingestion and handles REST API edge cases (403 Rate Limits, 410 Expired Artifacts, Malformed XML).
- **Presentation:** Decoupled interfaces featuring an interactive Typer/Rich CLI and a FastAPI REST endpoint.

## 🚀 Getting Started

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
Harvest artifacts from any public repository by providing the owner and repo name.
```bash
python harvester.py OVertly-Pleasant flaky-test-demo
```

**2. View in Terminal (CLI)**
Analyze the harvested SQLite database via terminal.
```bash
python main.py OVertly-Pleasant flaky-test-demo --top 10
```

**3. Serve via REST API**
```bash
uvicorn server:app --reload
```
Navigate to `http://localhost:8000/analyse?owner=OVertly-Pleasant&repo=flaky-test-demo` to view the JSON payload.

---
### ⚠️ Known Limitations
- **Same-Commit Retry Masking:** Currently disabled. Due to GitHub Actions v4 Artifact Immutability (Issue #323), re-running all jobs deletes previous artifacts for that commit. Until GitHub patches this upstream API behavior, the harvester cannot reliably capture multi-attempt variance on a single commit hash.
