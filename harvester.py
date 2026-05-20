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
    return response.json().get("artifacts", [])

def download_xml_from_artifact(download_url):
    """Downloads the ZIP, extracts it in memory, and returns the XML string."""
    response = requests.get(download_url, headers=HEADERS)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open("results.xml") as xml_file:
            return xml_file.read()

def parse_test_results(xml_string):
    """Parses JUnit XML and returns a list of tuples: [(test_name, status), ...]"""
    root = ET.fromstring(xml_string)
    results = []
    
    for testsuite in root.findall('testsuite'):
        for testcase in testsuite.findall('testcase'):
            name = testcase.attrib.get('name')
            # If there is a <failure> tag inside the testcase, it failed.
            if testcase.find('failure') is not None:
                results.append((name, "Failed"))
            else:
                results.append((name, "Passed"))
                
    return results

def setup_database():
    """Creates the table if it doesn't exist."""
    conn = sqlite3.connect('commits.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            commit_hash TEXT,
            test_name TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_database(run_id, commit_hash, parsed_results):
    """Inserts a list of parsed results into SQLite."""
    conn = sqlite3.connect('commits.db')
    cursor = conn.cursor()
    
    data_to_insert = []
    for test_name, status in parsed_results:
        data_to_insert.append((run_id, commit_hash, test_name, status))
        
    cursor.executemany('''
        INSERT INTO test_runs(run_id, commit_hash, test_name, status) 
        VALUES(?, ?, ?, ?)
    ''', data_to_insert)
    
    conn.commit()
    conn.close()

@app.command()
def run_pipeline(owner:str, repo:str):
    setup_database()
    artifacts = get_artifacts_list(owner,repo)
    print(f"Found {len(artifacts)} artifacts to process in {owner}/{repo}.")
    
    for artifact in artifacts:
        run_id = artifact["workflow_run"]["id"]
        commit_hash = artifact["workflow_run"]["head_sha"]
        download_url = artifact["archive_download_url"]
        
        print(f"Processing Run ID: {run_id}...")
        
        # 1. Download XML
        xml_content = download_xml_from_artifact(download_url)
        # 2. Parse XML
        parsed_results = parse_test_results(xml_content)
        # 3. Save to DB
        save_to_database(run_id, commit_hash, parsed_results)
        
    print("Data harvesting complete!")

if __name__ == "__main__":
    app()