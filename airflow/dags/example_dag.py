from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def extract_op():
    print("Extracting data")

def transform_op():
    print("Transforming data")

def load_op():
    print("Loading data")

with DAG(
    dag_id="sandbox_dag",
    description="An example DAG for data processing",
    schedule="@daily",
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example", "airflow2.9"],
) as dag:
    task_1 = PythonOperator(
        task_id="extract_function",
        python_callable=extract_op,
    )

    task_2 = PythonOperator(
        task_id="transform_function",
        python_callable=transform_op,
    )

    task_3 = PythonOperator(
        task_id="load_function",
        python_callable=load_op,
    )

    task_1 >> task_2 >> task_3

