import os
import sqlite3
import pandas as pd

def score_flip_rate(df):
    df_sorted = df.sort_values(by=['test_name', 'run_at'])
    df_sorted['prev_passed'] = df_sorted.groupby('test_name')['passed'].shift(1)
    df_sorted['is_flip'] = (df_sorted['passed'] != df_sorted['prev_passed']) & df_sorted['prev_passed'].notna()
    
    metrics = df_sorted.groupby('test_name').agg(
        total_runs=('passed', 'count'),
        pass_rate=('passed', 'mean'),
        total_flips=('is_flip', 'sum')
    )
    
    metrics['max_flips'] = metrics['total_runs'] - 1
    metrics['flip_score'] = metrics.apply(
        lambda row: row['total_flips'] / row['max_flips'] if row['max_flips'] > 0 else 0, 
        axis=1
    )
    return metrics[['total_runs', 'pass_rate', 'flip_score']].reset_index()

def score_duration_anomaly(df):
    duration_df = df.groupby(['test_name', 'status'])['duration_ms'].mean().unstack()
    
    if 'Passed' not in duration_df.columns or 'Failed' not in duration_df.columns:
        duration_df['duration_score'] = 0.0
    else:
        duration_df['duration_score'] = duration_df.apply(
            lambda row: min((row['Failed'] - row['Passed']) / 1000, 1.0) 
            if pd.notna(row['Failed']) and pd.notna(row['Passed']) and row['Failed'] > row['Passed'] 
            else 0.0, 
            axis=1
        )
        
    duration_df['duration_score'] = duration_df['duration_score'].fillna(0.0)
    return duration_df[['duration_score']].reset_index()

def score_time_correlation(df):
    """Detects if failures are clustered around a specific hour of the day."""
    failed_df = df[df['status'] == 'Failed'].copy()
    
    if failed_df.empty:
        return pd.DataFrame({'test_name': df['test_name'].unique(), 'time_score': [0.0] * df['test_name'].nunique()})

    failed_df['hour'] = pd.to_datetime(failed_df['run_at']).dt.hour
    
    time_metrics = failed_df.groupby('test_name').apply(
        lambda x: x['hour'].value_counts().max() / len(x)
    ).reset_index(name='time_score')
    
    all_tests = pd.DataFrame({'test_name': df['test_name'].unique()})
    return pd.merge(all_tests, time_metrics, on='test_name', how='left').fillna(0.0)

def generate_flakiness_report(max_results: int, db_path: str):
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM test_runs ORDER BY run_id ASC", conn)
    conn.close()

    run_counts = df['test_name'].value_counts()
    valid_tests = run_counts[run_counts >= 5].index
    df = df[df['test_name'].isin(valid_tests)]

    if df.empty:
        return pd.DataFrame()

    df['passed'] = df['status'] == 'Passed'

    flip_df = score_flip_rate(df)
    duration_df = score_duration_anomaly(df)
    time_df = score_time_correlation(df)

    report = pd.merge(flip_df, duration_df, on='test_name', how='outer')
    report = pd.merge(report, time_df, on='test_name', how='outer')

    report['ultimate_score'] = (report['flip_score'] + report['duration_score'] + report['time_score']) / 3

    final_report = report.sort_values('ultimate_score', ascending=False).head(max_results)
    
    return final_report.reset_index()