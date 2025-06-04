import json
import os
import pandas as pd


if os.getenv("AIRFLOW_HOME"):
    AIRFLOW_DATA_DIR = os.path.join(os.getenv("AIRFLOW_HOME", "/opt/airflow"), "data")
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
    AIRFLOW_DATA_DIR = os.path.join(PROJECT_ROOT, "data")

DATA_RAW_PATH = os.path.join(AIRFLOW_DATA_DIR, "raw")
DATA_PROCESSED_PATH = os.path.join(AIRFLOW_DATA_DIR, "processed")


def transform_season_results(year: int):
    """
    Transform the raw F1 season results data for a specific year.
    This function is intended to be used in an Airflow DAG.
    """
    raw_file_path = os.path.join(DATA_RAW_PATH, str(year), "season_data.json")
    processed_file_path_races = os.path.join(DATA_PROCESSED_PATH, str(year), "races.csv")
    processed_file_path_results = os.path.join(DATA_PROCESSED_PATH, str(year), "results.csv")

    print(f"Starting transformation for year {year} from {raw_file_path}")

    try:
        with open(raw_file_path, 'r') as f:
            raw_data = json.load(f)

        if not (raw_data and "MRData" in raw_data and "RaceTable" in raw_data["MRData"] and "Races" in
                raw_data["MRData"]["RaceTable"]):
            print(f"Raw data for year {year} is not in the expected format or is empty.")
            return False

        all_races_info = []
        all_circuits_details = []
        round_numbers = []
        seen_circuit_ids = set()

        races = raw_data["MRData"]["RaceTable"]["Races"]
        if not races:
            print(f"No races found for year {year}.")
            return False

        for race_info in races:
            circuit_info = race_info.get("Circuit", {})
            circuit_id = circuit_info.get("circuitId")
            if circuit_id and circuit_id not in seen_circuit_ids:
                location_info = circuit_info.get("Location", {})
                circuit_detail = {
                    "circuit_id": circuit_id,
                    "circuit_name": circuit_info.get("circuitName"),
                    "locality": location_info.get("locality"),
                    "country": location_info.get("country")
                }
                all_circuits_details.append(circuit_detail)
                seen_circuit_ids.add(circuit_id)

        if all_circuits_details:
            df_circuits = pd.DataFrame(all_circuits_details)
            os.makedirs(os.path.join(DATA_PROCESSED_PATH, str(year)), exist_ok=True)
            circuits_csv_path = os.path.join(DATA_PROCESSED_PATH, str(year), "circuits_info.csv")
            df_circuits.to_csv(circuits_csv_path, index=False)
            print(f"Circuits info for year {year} saved to {circuits_csv_path}")

        for race_index, race_info in enumerate(races):
            round_numbers.append(race_index+1)
            race_id = f"{year}_{race_info.get("round", str(race_index + 1))}"
            current_race_info = {
                "race_id": race_id,
                "year": int(race_info.get("season", year)),
                "round": int(race_info.get("round")),
                "race_name": race_info.get("raceName"),
                "circuit_id": race_info.get("Circuit", {}).get("circuitId"),
                "circuit_name_denorm": race_info.get("Circuit", {}).get("circuitName"),
                "circuit_locality_denorm": race_info.get("Circuit", {}).get("Location", {}).get("locality"),
                "circuit_country_denorm": race_info.get("Circuit", {}).get("Location", {}).get("country"),
                "date": race_info.get("date"),
                "time": race_info.get("time"),
            }
            all_races_info.append(current_race_info)

        df_races = pd.DataFrame(all_races_info)

        os.makedirs(os.path.join(DATA_PROCESSED_PATH, str(year)), exist_ok=True)

        races_csv_path = os.path.join(DATA_PROCESSED_PATH, str(year), "races_schedule.csv")
        df_races.to_csv(races_csv_path, index=False)
        print(f"Races for year {year} saved to {races_csv_path}.")

        return sorted(list(set(round_numbers)))
    except FileNotFoundError:
        print(f"Raw data file for year {year} not found at {raw_file_path}.")
        return False
    except Exception as e:
        print(f"An error occurred while transforming data for year {year}: {e}")
        return False

def transform_all_detailed_results_for_season(year: int, round_numbers: list):
    """
    Transform the raw F1 detailed results data for a specific year.
    """
    all_detailed_results = []
    all_drivers_data = []
    all_constructors_data = []
    seen_driver_ids = set()
    seen_constructor_ids = set()

    for round_num in round_numbers:
        raw_file_path = os.path.join(DATA_RAW_PATH, str(year), f"round_{round_num}_results.json")
        race_id_generated = f"{year}_{round_num}"

        try:
            with open(raw_file_path, 'r') as f:
                round_data = json.load(f)

            if not (round_data and "MRData" in round_data and "RaceTable" in round_data["MRData"] and "Races" in round_data["MRData"]["RaceTable"]):
                print(f"Round {round_num} data for year {year} is not in the expected format or is empty.")
                continue

            races_in_found_file = round_data["MRData"]["RaceTable"]["Races"]
            if not races_in_found_file:
                print(f"No race object found in round {round_num} data for year {year}.")
                continue

            race_results_list = races_in_found_file[0].get("Results", [])

            for result in race_results_list:
                driver_info = result.get("Driver", {})
                constructor_info = result.get("Constructor", {})
                time_info = result.get("Time", {})

                driver_id = driver_info.get("driverId")
                if driver_id and driver_id not in seen_driver_ids:

                    all_drivers_data.append({
                        "driver_id": driver_id,
                        "permanent_number": driver_info.get("permanentNumber"),
                        "code": driver_info.get("code"),
                        "given_name": driver_info.get("givenName"),
                        "family_name": driver_info.get("familyName"),
                        "date_of_birth": driver_info.get("dateOfBirth"),
                        "nationality": driver_info.get("nationality"),
                    })
                    seen_driver_ids.add(driver_id)

                constructor_id = constructor_info.get("constructorId")
                if constructor_id and constructor_id not in seen_constructor_ids:
                    print(f"→ Adding constructor_id = '{constructor_id}' from round {round_num}")
                    all_constructors_data.append({
                        "constructor_id": constructor_id,
                        "name": constructor_info.get("name"),
                        "nationality": constructor_info.get("nationality"),
                    })
                    seen_constructor_ids.add(constructor_id)

                detailed_result = {
                    "race_id": race_id_generated,
                    "driver_id": driver_id,
                    "constructor_id": constructor_id,
                    "car_number": result.get("number"),
                    "grid_position": int(result.get("grid", 0)),
                    "final_position": int(result.get("position", 0)) if result.get("position").isdigit() else None,
                    "position_text": result.get("positionText"),
                    "points": float(result.get("points", 0.0)),
                    "laps_completed": int(result.get("laps", 0)),
                    "status": result.get("status"),
                    "time_millis": time_info.get("millis"),
                    "time_text": time_info.get("time"),
                }
                all_detailed_results.append(detailed_result)
        except FileNotFoundError:
            print(f"Error: Results file not found for year {year}, round {round_num} at {raw_file_path}")
            continue
        except Exception as e:
            print(f"An error occurred processing results for year {year}, round {round_num}:")
            continue

    output_dir_year = os.path.join(DATA_PROCESSED_PATH, str(year))
    os.makedirs(output_dir_year, exist_ok=True)

    if all_detailed_results:
        df_detailed_results = pd.DataFrame(all_detailed_results)
        df_detailed_results.drop_duplicates(subset=['race_id', 'driver_id'], keep='first',
                                            inplace=True)
        results_csv_path = os.path.join(output_dir_year, "detailed_results.csv")
        df_detailed_results.to_csv(results_csv_path, index=False)
        print(f"Detailed results for year {year} saved to {results_csv_path}.")

    if all_drivers_data:
        df_drivers = pd.DataFrame(all_drivers_data)
        drivers_csv_path = os.path.join(output_dir_year, "drivers.csv")
        df_drivers.to_csv(drivers_csv_path, index=False)
        print(f"Drivers data for year {year} saved to {drivers_csv_path}.")

    if all_constructors_data:
        df_constructors = pd.DataFrame(all_constructors_data)
        constructors_csv_path = os.path.join(output_dir_year, "constructors.csv")
        df_constructors.to_csv(constructors_csv_path, index=False)
        print(f"Constructors data for year {year} saved to {constructors_csv_path}.")

    return True