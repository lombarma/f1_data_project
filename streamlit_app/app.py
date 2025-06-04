# f1_data_project/streamlit_app/app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

st.set_page_config(layout="wide", page_title="Dashboard F1 Insights")

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "airflow")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASSWORD = os.getenv("DB_PASSWORD", "airflow")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@st.cache_resource
def init_db_engine():
    """Initialize the database engine with a connection timeout."""
    try:
        engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 5})
        with engine.connect() as connection:
            pass
        return engine
    except Exception as e:
        print(f"Connexion error to the database: {e}")
        return None


def load_data_from_db(query: str, db_engine):
    """Load data from the database using a SQL query."""
    if db_engine is None:
        st.error("Impossible to load data: database engine is not initialized.")
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, db_engine)
        return df
    except Exception as e:
        st.error(f"Error while loading the data: {e}")
        return pd.DataFrame()


engine = init_db_engine()

st.title("🏎️ F1 Insights Dashboard")

if engine:
    st.sidebar.success("Connected to the database !")

    st.sidebar.header("Filters")

    selected_year = None
    selected_round_for_results = None

    try:
        available_years_df = load_data_from_db("SELECT DISTINCT year FROM races ORDER BY year DESC;", engine)
        if not available_years_df.empty:
            available_years = available_years_df["year"].tolist()
            selected_year = st.sidebar.selectbox("Select a season :", available_years,
                                                 index=0 if available_years else None)
        else:
            st.sidebar.warning("No data available for any season.")
    except Exception as e:
        st.sidebar.error(f"Impossible to load data: {e}")

    if selected_year:
        st.header(f"Data for the season {selected_year}")

        st.subheader("Races Schedule")
        races_query = f"SELECT round, race_name, date, circuit_name_denorm as circuit FROM races WHERE year = {selected_year} ORDER BY round;"
        df_races_year = load_data_from_db(races_query, engine)

        if not df_races_year.empty:
            st.dataframe(df_races_year, use_container_width=True)

            race_options = {f"Round {row['round']} - {row['race_name']}": row['round']
                            for index, row in df_races_year.iterrows()}

            if race_options:
                selected_race_display_name = st.sidebar.selectbox(
                    "Select a race to see results:",
                    list(race_options.keys()),
                    index=0
                )
                selected_round_for_results = race_options[selected_race_display_name]
            else:
                st.sidebar.warning("No races available for this season.")

        else:
            st.warning(f"No race found for the season {selected_year}.")

        if selected_round_for_results is not None:
            st.subheader(f"Results for : {selected_race_display_name}")
            results_query = f"""
                        SELECT 
                            res.final_position as position, 
                            d.given_name || ' ' || d.family_name as driver, 
                            c.name as constructor,
                            res.points,
                            res.status
                        FROM results res
                        JOIN races r ON res.race_id = r.race_id
                        JOIN drivers d ON res.driver_id = d.driver_id
                        JOIN constructors c ON res.constructor_id = c.constructor_id
                        WHERE r.year = {selected_year} AND r.round = {selected_round_for_results} 
                        ORDER BY res.final_position ASC NULLS LAST, res.points DESC;
                    """
            df_results_selected_race = load_data_from_db(results_query, engine)

            if not df_results_selected_race.empty:
                st.dataframe(df_results_selected_race, use_container_width=True)

                if 'driver' in df_results_selected_race.columns and 'points' in df_results_selected_race.columns:
                    points_chart_data = \
                    df_results_selected_race[df_results_selected_race['points'] > 0].set_index('driver')['points']
                    if not points_chart_data.empty:
                        st.subheader("Scored Points by Driver for the selected race")
                        st.bar_chart(points_chart_data)
            else:
                st.warning(f"No results for {selected_race_display_name}.")
        elif selected_year:
            st.info("Select a race in the sidebar to view results.")

    elif engine:
        st.info("Select a season in the sidebar to view")

else:
    st.error(
        "Database connection failed. Please check your environment variables or database settings.")
    st.sidebar.error("Failed to connect to F1 database")

st.sidebar.markdown("---")
st.sidebar.markdown("Projet F1 Insights")