import os
import sqlite3
import pandas as pd

def generate_flakiness_report(max_results: int, db_path: str):
    """
    Analyzes test runs using Google's Transition Count (Flip Rate) model.
    """
    if not os.path.exists(db_path):
        return pd.DataFrame(columns=['test_name', 'pass_rate', 'flakiness'])

    conn = sqlite3.connect(db_path)
    query = "SELECT test_name, status, run_id FROM test_runs ORDER BY run_id ASC"
    test_runs_df = pd.read_sql_query(query, conn)
    conn.close()

    if test_runs_df.empty:
        return pd.DataFrame(columns=['test_name', 'pass_rate', 'flakiness'])

    test_runs_df['passed'] = test_runs_df['status'] == 'Passed'

    test_runs_df = test_runs_df.sort_values(by=['test_name', 'run_id'])

    test_runs_df['prev_passed'] = test_runs_df.groupby('test_name')['passed'].shift(1)

    # 'Flip' occurs if the current status doesn't match the previous status
    # used notna() so don't count the very first run as a flip
    test_runs_df['is_flip'] = (test_runs_df['passed'] != test_runs_df['prev_passed']) & test_runs_df['prev_passed'].notna()

    metrics_df = test_runs_df.groupby('test_name').agg(
        total_runs=('passed', 'count'),
        pass_rate=('passed', 'mean'),
        total_flips=('is_flip', 'sum')
    )
    # Calculate Flip Rate (Flakiness Score)
    # Max possible flips is (total runs - 1)
    metrics_df['max_flips'] = metrics_df['total_runs'] - 1
    # Avoid division by zero if a test only ran once
    metrics_df['flakiness'] = metrics_df.apply(
        lambda row: row['total_flips'] / row['max_flips'] if row['max_flips'] > 0 else 0, 
        axis=1
    )
    final_report = metrics_df.sort_values('flakiness', ascending=False).head(max_results)
    
    return final_report.reset_index()