from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from pipeline import (
    run_schema,
    run_seed,
    run_instruments,
    run_classify,
    run_quotes,
    run_indicators,
    run_signals,
    run_effectiveness,
    run_stats,
)

default_args = {
    "owner": "stocker",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stocker_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 6 * * *",
    catchup=False,
    default_args=default_args,
    description="StockerByAI daily pipeline",
) as dag:

    schema = PythonOperator(task_id="schema", python_callable=run_schema)
    seed = PythonOperator(task_id="seed", python_callable=run_seed)
    instruments = PythonOperator(task_id="instruments", python_callable=run_instruments)
    classify = PythonOperator(task_id="classify", python_callable=run_classify)
    quotes = PythonOperator(task_id="quotes", python_callable=run_quotes)
    indicators = PythonOperator(task_id="indicators", python_callable=run_indicators)
    signals = PythonOperator(task_id="signals", python_callable=run_signals)
    effectiveness = PythonOperator(task_id="effectiveness", python_callable=run_effectiveness)
    stats = PythonOperator(task_id="stats", python_callable=run_stats)

    schema >> seed >> instruments >> classify >> quotes
    quotes >> indicators >> signals
    signals >> effectiveness >> stats