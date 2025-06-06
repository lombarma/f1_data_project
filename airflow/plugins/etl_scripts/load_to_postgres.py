#!/usr/bin/env python3
import os
import sys
import argparse
import psycopg2
import pandas as pd


def get_data_paths(year: int):
    """
    Rebuild paths to the processed CSV files for a given year.
    """
    if os.getenv("AIRFLOW_HOME"):
        airflow_home = os.getenv("AIRFLOW_HOME")
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
        airflow_home = project_root

    data_processed_path = os.path.join(airflow_home, "data", "processed", str(year))
    return {
        "circuits":     os.path.join(data_processed_path, "circuits_info.csv"),
        "races":        os.path.join(data_processed_path, "races_schedule.csv"),
        "drivers":      os.path.join(data_processed_path, "drivers.csv"),
        "constructors": os.path.join(data_processed_path, "constructors.csv"),
        "results":      os.path.join(data_processed_path, "detailed_results.csv"),
    }


def connect_to_postgres():
    """
    Open a connection to PostgreSQL using environment variables.
    """
    pg_host     = os.getenv("PG_HOST", "localhost")
    pg_port     = os.getenv("PG_PORT", "5432")
    pg_db       = os.getenv("PG_DATABASE")
    pg_user     = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")

    if not (pg_db and pg_user and pg_password):
        print("❗ ERROR : Environment variables PG_DATABASE, PG_USER and PG_PASSWORD must be set.")
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            dbname=pg_db,
            user=pg_user,
            password=pg_password
        )
        return conn
    except Exception as e:
        print(f"❗ PostgreSQL Connexion Error : {e}")
        sys.exit(1)


def upsert_circuits(cursor, csv_path: str):
    """
    Read circuits_info.csv and do INSERT ... ON CONFLICT DO NOTHING.
    """
    if not os.path.isfile(csv_path):
        print(f"⚠️  Fichier circuits manquant, skip: {csv_path}")
        return

    df = pd.read_csv(csv_path, dtype=str)
    sql = """
        INSERT INTO circuits (circuit_id, circuit_name, locality, country)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (circuit_id) DO NOTHING;
    """
    for _, row in df.iterrows():
        cursor.execute(sql, (
            row["circuit_id"],
            row.get("circuit_name"),
            row.get("locality"),
            row.get("country"),
        ))
    print(f"✔️  Upsert terminé pour {os.path.basename(csv_path)} → circuits")


def upsert_drivers(cursor, csv_path: str):
    """
    Read drivers.csv and do INSERT ... ON CONFLICT DO NOTHING.
    """
    if not os.path.isfile(csv_path):
        print(f"⚠️  Fichier drivers manquant, skip: {csv_path}")
        return

    df = pd.read_csv(csv_path, dtype=str)
    sql = """
        INSERT INTO drivers (
            driver_id, permanent_number, code,
            given_name, family_name, date_of_birth, nationality
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (driver_id) DO NOTHING;
    """
    for _, row in df.iterrows():
        cursor.execute(sql, (
            row["driver_id"],
            row.get("permanent_number"),
            row.get("code"),
            row.get("given_name"),
            row.get("family_name"),
            row.get("date_of_birth"),
            row.get("nationality"),
        ))
    print(f"✔️  Upsert terminé pour {os.path.basename(csv_path)} → drivers")


def upsert_constructors(cursor, csv_path: str):
    """
    and do constructors.csv and do INSERT ... ON CONFLICT DO NOTHING.
    """
    if not os.path.isfile(csv_path):
        print(f"⚠️  Fichier constructors manquant, skip: {csv_path}")
        return

    df = pd.read_csv(csv_path, dtype=str)
    sql = """
        INSERT INTO constructors (constructor_id, name, nationality)
        VALUES (%s, %s, %s)
        ON CONFLICT (constructor_id) DO NOTHING;
    """
    for _, row in df.iterrows():
        cursor.execute(sql, (
            row["constructor_id"],
            row.get("name"),
            row.get("nationality"),
        ))
    print(f"✔️  Upsert terminé pour {os.path.basename(csv_path)} → constructors")


def upsert_races(cursor, csv_path: str):
    """
    Read races_schedule.csv and do INSERT ... ON CONFLICT DO NOTHING sur race_id.
    """
    if not os.path.isfile(csv_path):
        print(f"⚠️  Fichier races manquant, skip: {csv_path}")
        return

    df = pd.read_csv(csv_path, dtype=str)
    sql = """
        INSERT INTO races (
            race_id, year, round, race_name, circuit_id,
            circuit_name_denorm, circuit_locality_denorm,
            circuit_country_denorm, date, time
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (race_id) DO NOTHING;
    """
    for _, row in df.iterrows():
        cursor.execute(sql, (
            row["race_id"],
            row.get("year"),
            row.get("round"),
            row.get("race_name"),
            row.get("circuit_id"),
            row.get("circuit_name_denorm"),
            row.get("circuit_locality_denorm"),
            row.get("circuit_country_denorm"),
            row.get("date"),
            row.get("time"),
        ))
    print(f"✔️  Upsert terminé pour {os.path.basename(csv_path)} → races")


def upsert_results(cursor, csv_path: str):
    """
    Read detailed_results.csv and do INSERT ... ON CONFLICT DO NOTHING
    based on unique constraint (race_id, driver_id).
    """
    if not os.path.isfile(csv_path):
        print(f"⚠️  Fichier results manquant, skip: {csv_path}")
        return

    df = pd.read_csv(csv_path, dtype=str)
    sql = """
        INSERT INTO results (
            race_id, driver_id, constructor_id, car_number,
            grid_position, final_position, position_text,
            points, laps_completed, status, time_millis, time_text
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (race_id, driver_id) DO NOTHING;
    """
    for _, row in df.iterrows():
        car_number      = int(row["car_number"]) if row.get("car_number") and row["car_number"].isdigit() else None
        grid_position   = int(row["grid_position"]) if row.get("grid_position") and row["grid_position"].isdigit() else None
        final_position  = int(row["final_position"]) if row.get("final_position") and row["final_position"].isdigit() else None
        points          = float(row["points"]) if row.get("points") else None
        laps_completed  = int(row["laps_completed"]) if row.get("laps_completed") and row["laps_completed"].isdigit() else None

        cursor.execute(sql, (
            row["race_id"],
            row["driver_id"],
            row["constructor_id"],
            car_number,
            grid_position,
            final_position,
            row.get("position_text"),
            points,
            laps_completed,
            row.get("status"),
            row.get("time_millis"),
            row.get("time_text"),
        ))
    print(f"✔️  Upsert terminé pour {os.path.basename(csv_path)} → results")


def load_year_into_postgres(year: int):
    """
    Load in an indopendent year of F1 data into PostgreSQL.
    """
    conn   = connect_to_postgres()
    cursor = conn.cursor()
    paths  = get_data_paths(year)

    # 1. Circuits (UPSERT)
    upsert_circuits(cursor, paths["circuits"])

    # 2. Races (UPSERT)
    upsert_races(cursor, paths["races"])

    # 3. Drivers (UPSERT)
    upsert_drivers(cursor, paths["drivers"])

    # 4. Constructors (UPSERT)
    upsert_constructors(cursor, paths["constructors"])

    # 5. Results (UPSERT)
    upsert_results(cursor, paths["results"])

    try:
        conn.commit()
        print(f"\n🎉 Loading done for the year: {year}.")
    except Exception as e:
        conn.rollback()
        print(f"❗ ERROR while commit : {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load F1 data for a specific season into PostgreSQL database."
    )
    parser.add_argument(
        "year", type=int,
        help="The F1 season year to load into PostgreSQL (e.g., 2023)."
    )
    args = parser.parse_args()
    year = args.year
    print(f"🔄 Beginning of the loading for {year}...\n")
    load_year_into_postgres(year)


if __name__ == "__main__":
    main()
