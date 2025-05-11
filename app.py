import streamlit as st
import pandas as pd
import googlemaps
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# === CHARGER LA CLÉ API DEPUIS .env ===
load_dotenv()
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=google_maps_api_key)

# === CHARGER LES DONNÉES TECHNICIENS & PROJETS ===
with open("techniciens.json") as f:
    techniciens = json.load(f)
tech_names = [t["name"] for t in techniciens]

with open("projets.json") as f:
    projets = json.load(f)
project_names = [p["name"] for p in projets]

# === OUTILS ===
def get_distance_km(origin, destination):
    try:
        result = gmaps.distance_matrix(origin, destination, mode="driving")
        meters = result["rows"][0]["elements"][0]["distance"]["value"]
        return round(meters / 1000, 2)
    except:
        return None

def get_tech_address(name):
    return next((t["home_address"] for t in techniciens if t["name"] == name), None)

def get_project_address(name):
    return next((p["address"] for p in projets if p["name"] == name), None)

# === INIT SESSION ===
if "weekly_results" not in st.session_state:
    st.session_state["weekly_results"] = []

# === SIDEBAR : VIDER LE TABLEAU ===
st.sidebar.title("Options")
if st.sidebar.button("🧹 Vider le tableau des résultats"):
    st.session_state["weekly_results"] = []
    st.rerun()

# === INTERFACE PRINCIPALE ===
st.title("🚌 Calcul Hebdomadaire du Transport à Compenser")

# Semaine sélectionnée
selected_date = st.date_input("📅 Choisissez une date de la semaine : ", value=datetime.today())
start_date = selected_date - timedelta(days=selected_date.weekday())
jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
dates_semaine = [start_date + timedelta(days=i) for i in range(5)]

for i, jour in enumerate(jours):
    date_jour = dates_semaine[i]
    st.subheader(jour)
    with st.expander(f"{jour} ({date_jour.strftime('%Y-%m-%d')})"):
        nb = st.number_input(f"Nombre de techniciens pour {jour}", min_value=1, max_value=10, key=f"nb_{jour}")
        for j in range(nb):
            cols = st.columns([2, 3, 3])
            with cols[0]:
                tech = st.selectbox("Technicien", tech_names, key=f"{jour}_tech_{j}")
            with cols[1]:
                projet_matin = st.selectbox("Projet matin", project_names, key=f"{jour}_matin_proj_{j}")
                addr_matin = get_project_address(projet_matin)
            with cols[2]:
                projet_soir = st.selectbox("Projet soir", project_names, key=f"{jour}_soir_proj_{j}")
                addr_soir = get_project_address(projet_soir)

            # Ajouter ce trajet manuellement
            if st.button("✅ Ajouter ce trajet", key=f"{jour}_{j}_add"):
                if tech and addr_matin and addr_soir:
                    home = get_tech_address(tech)
                    dist_matin = get_distance_km(home, addr_matin)
                    dist_soir = get_distance_km(addr_soir, home)

                    comp_matin = max(0, dist_matin - 40) if dist_matin else 0
                    comp_soir = max(0, dist_soir - 40) if dist_soir else 0
                    total_comp = round(comp_matin + comp_soir, 2)

                    st.session_state["weekly_results"].append({
                        "Date": date_jour.strftime('%Y-%m-%d'),
                        "Technicien": tech,
                        "Projet Matin": projet_matin,
                        "Projet Soir": projet_soir,
                        "Adresse Matin": addr_matin,
                        "Adresse Soir": addr_soir,
                        "Distance Matin (km)": dist_matin,
                        "Distance Soir (km)": dist_soir,
                        "Km à Compenser": total_comp
                    })
                    st.success(f"✅ Trajet ajouté pour {tech} le {jour}.")

# === RÉCAPITULATIF HEBDOMADAIRE ===
if st.session_state["weekly_results"]:
    df = pd.DataFrame(st.session_state["weekly_results"])
    st.subheader("📋 Récapitulatif de la semaine")
    st.dataframe(df, use_container_width=True)
