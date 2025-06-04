# f1_data_project/streamlit_app/app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# 1. st.set_page_config() DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(layout="wide", page_title="Dashboard F1 Insights")

# --- Configuration de la Connexion à la Base de Données ---
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "airflow")
DB_USER = os.getenv("DB_USER", "airflow")
DB_PASSWORD = os.getenv("DB_PASSWORD", "airflow")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# --- Fonctions ---
@st.cache_resource  # Garder le cache pour le moteur
def init_db_engine():
    """Initialise et retourne le moteur SQLAlchemy."""
    try:
        engine = create_engine(DATABASE_URL, connect_args={'connect_timeout': 5})
        with engine.connect() as connection:  # Test de la connexion
            pass
        return engine
    except Exception as e:
        print(f"Erreur de connexion à la base de données lors de l'initialisation: {e}")
        return None


def load_data_from_db(query: str, db_engine):
    """Charge les données depuis la base de données en utilisant une requête SQL."""
    if db_engine is None:
        st.error("Impossible de charger les données : aucune connexion à la base de données.")
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, db_engine)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()


# --- Initialisation du Moteur et Interface Utilisateur Principale ---
engine = init_db_engine()

st.title("🏎️ F1 Insights Dashboard")

if engine:
    st.sidebar.success("Connecté à la base de données F1 !")  # Message de succès déplacé ici

    st.sidebar.header("Filtres")

    selected_year = None
    selected_round_for_results = None  # Initialiser la variable pour le round sélectionné

    try:
        available_years_df = load_data_from_db("SELECT DISTINCT year FROM races ORDER BY year DESC;", engine)
        if not available_years_df.empty:
            available_years = available_years_df["year"].tolist()
            selected_year = st.sidebar.selectbox("Choisissez une saison :", available_years,
                                                 index=0 if available_years else None)
        else:
            st.sidebar.warning("Aucune année disponible dans la table 'races'.")
    except Exception as e:
        st.sidebar.error(f"Impossible de charger les années : {e}")

    if selected_year:
        st.header(f"Données pour la saison {selected_year}")

        st.subheader("Calendrier des Courses")
        races_query = f"SELECT round, race_name, date, circuit_name_denorm as circuit FROM races WHERE year = {selected_year} ORDER BY round;"
        df_races_year = load_data_from_db(races_query, engine)

        if not df_races_year.empty:
            st.dataframe(df_races_year, use_container_width=True)

            # --- AJOUT DU SÉLECTEUR DE COURSE ---
            # Créer les options pour le selectbox des courses
            # On stocke le numéro du round avec le nom pour pouvoir l'utiliser dans la requête
            race_options = {f"Round {row['round']} - {row['race_name']}": row['round']
                            for index, row in df_races_year.iterrows()}

            if race_options:
                selected_race_display_name = st.sidebar.selectbox(
                    "Choisissez une course pour voir les résultats :",
                    list(race_options.keys()),
                    index=0  # Sélectionne la première course par défaut
                )
                selected_round_for_results = race_options[selected_race_display_name]
            else:
                st.sidebar.warning("Aucune course à sélectionner pour cette saison.")
            # --- FIN DE L'AJOUT DU SÉLECTEUR DE COURSE ---

        else:
            st.warning(f"Aucune course trouvée pour la saison {selected_year}.")

        if selected_round_for_results is not None:
            st.subheader(f"Résultats pour : {selected_race_display_name}")
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
                        st.subheader("Points Marqués pour cette Course")
                        st.bar_chart(points_chart_data)
            else:
                st.warning(f"Aucun résultat trouvé pour {selected_race_display_name}.")
        elif selected_year:  # Si une année est sélectionnée mais pas de round (par ex. si df_races_year était vide)
            st.info("Sélectionnez une course dans la barre latérale pour afficher ses résultats.")

    elif engine:
        st.info("Veuillez sélectionner une saison pour afficher les données.")

else:
    st.error(
        "La connexion à la base de données a échoué. Veuillez vérifier les logs du conteneur Streamlit et la configuration de la base de données.")
    st.sidebar.error("Échec de la connexion à la base de données F1.")  # Message d'erreur déplacé ici

st.sidebar.markdown("---")
st.sidebar.markdown("Projet F1 Insights")