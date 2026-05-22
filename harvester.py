import os
import requests
import zipfile
import io
import sqlite3
import typer
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

app = typer.Typer()
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_artifacts_list(owner: str, repo: str):
    """Fetches the list of artifacts from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 403:
        print("GitHub API Rate Limit Exceeded! Check your token or try again later.")
        return []
    elif response.status_code != 200:
        print(f"Failed to fetch artifacts: HTTP {response.status_code}")
        return []  
    return response.json().get("artifacts", [])

def download_xml_from_artifact(download_url):
    """Downloads the ZIP, extracts it in memory, and returns the XML string."""
    response = requests.get(download_url, headers=HEADERS)
    if response.status_code == 410:
        print("Artifact has expired and been deleted by GitHub. Skipping...")
        return None
        
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        if "results.xml" not in z.namelist():
            print("results.xml not found in this artifact. Skipping...")
            return None
            
        with z.open("results.xml") as xml_file:
            return xml_file.read()

def parse_junit_xml(xml_string):
    """Parses JUnit XML and extracts test status, duration, and execution order."""
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        print("Malformed XML found. Skipping parse...")
        return []

    results = []
    
    for position, testcase in enumerate(root.iter('testcase'), start=1):
        test_name = testcase.attrib.get('name')
        time_sec = float(testcase.attrib.get('time', 0))
        duration_ms = int(time_sec * 1000)
        status = "Failed" if testcase.find('failure') is not None else "Passed" 
        results.append((test_name, status, duration_ms, position))
                
    return results

def setup_database(db_name):
    """Creates the table if it doesn't exist."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_runs (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id        INTEGER,
        commit_hash   TEXT,
        test_name     TEXT,
        status        TEXT,
        run_at        TEXT,
        duration_ms   INTEGER,
        position      INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_test_runs(db_name, run_id, commit_hash, run_timestamp, parsed_results):
    """Inserts a list of parsed results into SQLite."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    data_to_insert = []
    for test_name, status, duration_ms, position in parsed_results:
        data_to_insert.append((
            run_id, commit_hash, test_name, status, run_timestamp, duration_ms, position
        ))
        
    cursor.executemany('''
        INSERT INTO test_runs(run_id, commit_hash, test_name, status, run_at, duration_ms, position) 
        VALUES(?, ?, ?, ?, ?, ?, ?)
    ''', data_to_insert)
    
    conn.commit()
    conn.close()

def is_run_harvested(db_name, run_id):
    """Checks if a run_id already exists in the database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM test_runs WHERE run_id = ?", (run_id,))
    # fetchone() returns None if the row doesn't exist
    exists = cursor.fetchone() is not None 
    conn.close()
    return exists

@app.command()
def run_pipeline(owner:str, repo:str):
    db_name = f"{owner}_{repo}.db"
    setup_database(db_name)
    artifacts = get_artifacts_list(owner,repo)

    if not artifacts:
        print("No artifacts to process. Exiting.")
        return

    print(f"Found {len(artifacts)} artifacts to process in {owner}/{repo}.")

    for artifact in artifacts:
        run_id = artifact["id"]
        if is_run_harvested(db_name, run_id):
            print(f"Skipping Run {run_id} (Already in database).")
            continue
        
        commit_hash = artifact["workflow_run"]["head_sha"]
        run_timestamp = artifact["created_at"]
        download_url = artifact["archive_download_url"]

        print(f"Downloading & Processing Run ID: {run_id}...")

        # 1. Download XML
        xml_content = download_xml_from_artifact(download_url)
        if xml_content is None:
            continue
        # 2. Parse XML
        parsed_results = parse_junit_xml(xml_content)
        if not parsed_results:
            continue # Skip if XML was malformed or empty   
        # 3. Save to DB
        save_test_runs(db_name, run_id, commit_hash, run_timestamp, parsed_results)
        
    print("Data harvesting complete!")

if __name__ == "__main__":
    app()