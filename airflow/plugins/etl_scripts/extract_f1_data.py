import requests
import json
import os

BASE_API_URL = "https://ergast.com/api/f1"

if os.getenv("AIRFLOW_HOME"):
    DATA_RAW_PATH = os.path.join(os.getenv("AIRFLOW_HOME", "/opt/airflow"), "data", "raw")
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(
        os.path.join(SCRIPT_DIR, "..", "..", ".."))
    DATA_RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw")


def fetch_f1_data(year: int):
    """
    Fetch F1 data for a specific year
    """
    url = f"{BASE_API_URL}/{year}.json?limit=1000"
    print(f"Fetching F1 data for season {year} from {url}...")
    print(f"Data will be saved relative to: {DATA_RAW_PATH}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    output_dir_for_year = os.path.join(DATA_RAW_PATH, str(year))
    os.makedirs(output_dir_for_year, exist_ok=True)
    file_path = os.path.join(output_dir_for_year, "season_data.json")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data for season {year} saved to {file_path}")

    return data


def fetch_race_results(year: int,
                       round_num: int):
    """
    Fetch F1 data for a specific season and round.
    """
    url = f"{BASE_API_URL}/{year}/{round_num}/results.json"
    print(f"Fetching F1 race results for {year} round {round_num} from {url}...")
    print(f"Data will be saved relative to: {DATA_RAW_PATH}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    output_dir_for_year = os.path.join(DATA_RAW_PATH, str(year))
    os.makedirs(output_dir_for_year, exist_ok=True)
    file_path = os.path.join(output_dir_for_year, f"round_{round_num}_results.json")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Results for round {round_num} of season {year} saved to {file_path}")

    return data


if __name__ == "__main__":
    print(f"--- Running {__file__} in local test mode ---")
    print(f"--- DATA_RAW_PATH (for local) set to: {DATA_RAW_PATH} ---")

    if not os.path.exists(DATA_RAW_PATH):
        os.makedirs(DATA_RAW_PATH)
        print(f"Created base data directory for local test: {DATA_RAW_PATH}")

    year_to_test = 2023
    fetch_f1_data(year_to_test)

    round_to_test = 1
    fetch_race_results(year_to_test, round_to_test)
    print(f"--- Local test finished ---")