# F1 Data Project

This project extracts Formula 1 data from the Ergast API, processes it using Apache Airflow, stores it in a PostgreSQL database, and visualizes it with a Streamlit application.

## Project Structure

```
.
├── airflow/
│   ├── dags/
│   │   ├── f1_pipeline.py  # Airflow DAG for data extraction, transformation, and loading
│   │   └── ...
│   ├── logs/               # Airflow task logs
│   └── plugins/
│       └── etl_scripts/    # Python scripts for ETL processes
│           ├── extract_f1_data.py
│           ├── transform_f1_data.py
│           └── load_to_postgres.py
├── data/
│   ├── processed/          # Processed data (e.g., CSV files)
│   └── raw/                # Raw data from the API
├── postgres/
│   └── init.sql            # PostgreSQL initialization script (creates tables)
├── streamlit_app/
│   ├── app.py              # Streamlit application code
│   ├── Dockerfile          # Dockerfile for the Streamlit app
│   └── requirements.txt    # Python dependencies for the Streamlit app
├── docker-compose.yml      # Docker Compose configuration for all services
└── README.md               # This file
```

## Services

The project uses Docker Compose to manage the following services:

1.  **`postgres`**: PostgreSQL database to store F1 data.

    - Image: `postgres:15`
    - Port: `5432:5432`
    - Data is persisted in the `postgres_data_2_9` volume.
    - An initialization script `postgres/init.sql` is run on startup to create the necessary tables.

2.  **`pgadmin`**: pgAdmin for managing the PostgreSQL database.

    - Image: `dpage/pgadmin4:latest`
    - Port: `5050:80` (Access via `http://localhost:5050`)
    - Default credentials: `admin@admin.com` / `admin`

3.  **`airflow-init`**: Initializes the Airflow metadata database.

    - Image: `apache/airflow:2.9.2`
    - Runs database migrations and creates an admin user.

4.  **`airflow-webserver`**: Airflow web interface.

    - Image: `apache/airflow:2.9.2`
    - Port: `8080:8080` (Access via `http://localhost:8080`)
    - Default credentials: `admin` / `admin` (after `airflow-init` completes)
    - DAGs from `./airflow/dags` are mounted into the container.

5.  **`airflow-scheduler`**: Airflow scheduler to run DAGs.

    - Image: `apache/airflow:2.9.2`
    - Monitors and triggers tasks based on their schedules.

6.  **`streamlit`**: Streamlit application for data visualization.
    - Built from `./streamlit_app/Dockerfile`
    - Port: `8501:8501` (Access via `http://localhost:8501`)
    - Connects to the `postgres` service to fetch data.

## Airflow DAG: `f1_data_extraction_pipeline`

Located in `airflow/dags/f1_pipeline.py`, this DAG performs the following tasks:

1.  **`fetch_season_schedule_data`**: Fetches the season schedule (list of races) for a given year from the Ergast API.
    - The year can be specified as a parameter when triggering the DAG (default: 2024).
2.  **`transform_schedule_and_get_rounds`**: Transforms the raw season schedule data and extracts a list of round numbers for that season. This list is passed via XCom.
3.  **`fetch_all_round_details`**: For each round number obtained from the previous task, fetches detailed race results (qualifying, race results, etc.).
4.  **`transform_all_detailed_results`**: Transforms the raw detailed results for all rounds of the season.
5.  **`load_data_to_postgres`**: Loads the transformed data (races, results, drivers, constructors, etc.) into the PostgreSQL database.

The DAG is designed to be run manually for a specific year.

## Streamlit Application

Located in `streamlit_app/app.py`, this application provides a dashboard to visualize F1 data.

- Connects to the PostgreSQL database.
- Allows users to select a season.
- Displays the race calendar for the selected season.
- Allows users to select a specific race from the calendar.
- Displays detailed results for the selected race, including a bar chart of points scored by drivers.

## Setup and Usage

1.  **Prerequisites**:

    - Docker
    - Docker Compose

2.  **Build and Run**:

    ```bash
    docker-compose up --build -d
    ```

    This command will build the images (if not already built) and start all services in detached mode.

3.  **Access Services**:

    - **Airflow**: `http://localhost:8080` (Login: `admin` / `admin`)
    - **pgAdmin**: `http://localhost:5050` (Login: `admin@admin.com` / `admin`)
      - When setting up the server in pgAdmin, use `postgres` as the hostname/address, port `5432`, database `airflow`, username `airflow`, and password `airflow`.
    - **Streamlit App**: `http://localhost:8501`

4.  **Run Airflow DAG**:

    - Go to the Airflow UI (`http://localhost:8080`).
    - Unpause the `f1_data_extraction_pipeline` DAG.
    - Trigger the DAG manually, optionally specifying the `year_to_fetch` parameter.

5.  **View Data in Streamlit**:
    - Once the DAG has successfully run and populated the database, open the Streamlit app (`http://localhost:8501`).
    - Select a season and a race to view the data.

## Data Flow

1.  **Ergast API**: Source of F1 data.
2.  **Airflow (`f1_pipeline.py`)**:
    - Extracts data using scripts in `airflow/plugins/etl_scripts/extract_f1_data.py`.
    - Transforms data using scripts in `airflow/plugins/etl_scripts/transform_f1_data.py`.
    - Loads data into PostgreSQL using scripts in `airflow/plugins/etl_scripts/load_to_postgres.py`.
3.  **PostgreSQL**: Stores the structured F1 data. Tables are defined in `postgres/init.sql`.
4.  **Streamlit (`streamlit_app/app.py`)**: Queries the PostgreSQL database and presents the data in an interactive dashboard.

## Stopping the Application

```bash
docker-compose down
```

To remove volumes (and lose all data):

```bash
docker-compose down -v
```

## Future Improvements

- Add more visualizations to the Streamlit app (e.g., driver standings, constructor standings).
- Implement automated DAG runs for new seasons or recent races.
- Add more detailed data extraction (e.g., lap times, pit stops).
- Enhance error handling and logging.
