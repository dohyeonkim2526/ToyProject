from __future__ import annotations
import datetime
import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id="example_bash_operator", # dag's name
    schedule="0 0 * * *", # 매일 0시 0분에 실행
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"), # 2021년 1월 1일부터 실행
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60), # 60분이상 실행되면 timeout
    tags=["example", "example2"], # dag's tag
    params={"example_key": "example_value"},
) as dag:
    run_this_last = EmptyOperator( # 객체명
        task_id="run_this_last", # task's name
    )

    # [START howto_operator_bash]
    run_this = BashOperator(
        task_id="run_after_loop",
        bash_command="echo 1",
    )
    # [END howto_operator_bash]

    run_this >> run_this_last # task 수행순서
