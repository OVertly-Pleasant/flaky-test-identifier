import pandas as pd
import sqlite3


def connect_n_process(top:int,db:str):
    conn = sqlite3.connect(db)
    query = "SELECT test_name, status FROM test_runs"
    test_results = pd.read_sql_query(query, conn)
    conn.close()

    test_results['passed'] = test_results['status'] == 'Passed'
    pass_rate = test_results.groupby('test_name')['passed'].agg(
        pass_rate='mean', 
        total_runs='count'
    )
    pass_rate['flakiness'] = pass_rate['pass_rate'] * (1 - pass_rate['pass_rate'])
    pass_rate = pass_rate.sort_values('flakiness',ascending=False).head(top).reset_index()
    return pass_rate