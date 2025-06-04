import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
import ast
from etl_scripts.extract_f1_data import fetch_race_results, fetch_f1_data
from etl_scripts.transform_f1_data import transform_season_results, transform_all_detailed_results_for_season
from etl_scripts.load_to_postgres import load_year_into_postgres

DEFAULT_YEAR = 2024


def _fetch_all_rounds_callable(year: int, rounds_list_str: str, **kwargs):  # Renommé pour indiquer que c'est une chaîne
    """Call for fetching all rounds for a given year using the rounds_list_str from XCom."""

    if not rounds_list_str:
        print(
            f"Aucun round fourni pour l'année {year} (chaîne XCom vide ou None). Extraction des résultats de round sautée.")
        return

    print(f"Chaîne XCom brute pour rounds_list: '{rounds_list_str}'")

    actual_rounds_list = []
    try:
        parsed_value = ast.literal_eval(rounds_list_str)
        if isinstance(parsed_value, list):
            actual_rounds_list = parsed_value
        elif parsed_value is None:  # Si XCom était None, literal_eval retourne None
            print(f"La liste des rounds est None pour l'année {year} après parsing XCom. Extraction sautée.")
            return
        else:
            raise ValueError(f"La valeur XCom pour rounds_list n'est pas une liste après évaluation: {parsed_value}")

    except (ValueError, SyntaxError) as e:
        print(f"Erreur lors de l'analyse de la chaîne rounds_list ('{rounds_list_str}') depuis XCom. Erreur: {e}")
        raise ValueError(f"Impossible de parser rounds_list depuis XCom: '{rounds_list_str}'") from e

    if not actual_rounds_list:
        print(
            f"La liste des rounds est vide pour l'année {year} après parsing XCom. Extraction des résultats de round sautée.")
        return

    print(f"Extraction des résultats pour l'année {year}, rounds (liste parsée): {actual_rounds_list}")
    for r_num in actual_rounds_list:
        fetch_race_results(year=year, round_num=int(r_num))
    print(f"Extraction des résultats de tous les rounds terminée pour l'année {year}.")

def _load_to_postgres_callable(year: int, **kwargs):
    """
    Appel direct de la fonction Python 'load_year_into_postgres' définie dans load_to_postgres.py
    """
    if not year:
        raise ValueError("Le paramètre 'year' doit être fourni.")
    load_year_into_postgres(int(year))
    print(f"✅ Chargement des données dans Postgres terminé pour la saison {year}.")

with DAG(dag_id="f1_data_extraction_pipeline",
    description="Extracting data from ergast api for F1 seasons and rounds",
    schedule=None,
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    catchup=False,
    tags=["f1_project", "extraction"],
    params={
        "year_to_fetch": DEFAULT_YEAR,
    }) as dag:
    task_fetch_season_data = PythonOperator(
        task_id="fetch_season_schedule_data",
        python_callable=fetch_f1_data,
        op_kwargs={
            "year": "{{ params.year_to_fetch }}",
        }
    )

    task_transform_season_schedule_and_get_rounds = PythonOperator(
        task_id="transform_schedule_and_get_rounds",
        python_callable=transform_season_results,
        op_kwargs={
            "year": "{{ params.year_to_fetch }}"
        }
    )

    task_fetch_all_round_details = PythonOperator(
        task_id="fetch_all_round_details",
        python_callable=_fetch_all_rounds_callable,
        op_kwargs={
            "year": "{{ params.year_to_fetch }}",
            "rounds_list_str": "{{ ti.xcom_pull(task_ids='transform_schedule_and_get_rounds') }}"
        }
    )


    task_transform_all_detailed_results = PythonOperator(
        task_id="transform_all_detailed_results",
        python_callable=transform_all_detailed_results_for_season,
        op_kwargs={
            "year": "{{ params.year_to_fetch }}",
            "round_numbers": "{{ ti.xcom_pull(task_ids='transform_schedule_and_get_rounds') }}"
        }
    )

    task_load_data_to_db = PythonOperator(
        task_id="load_data_to_postgres",
        python_callable=_load_to_postgres_callable,
        op_kwargs={"year": "{{ params.year_to_fetch }}"},
    )

    task_fetch_season_data >> task_transform_season_schedule_and_get_rounds
    task_transform_season_schedule_and_get_rounds >> task_fetch_all_round_details
    task_fetch_all_round_details >> task_transform_all_detailed_results
    task_transform_all_detailed_results >> task_load_data_to_db