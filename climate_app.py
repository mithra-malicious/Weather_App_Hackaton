import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from streamlit_folium import st_folium
import folium

# 1. PAGE SETUP
st.set_page_config(page_title="T&T Climate Action Tool", layout="wide", page_icon="🇹🇹")

# 2. EXPANDED T&T LOCATIONS (North, Central, South, East, West & Tobago)
LOCATION_MAP = {
    # --- NORTH / NORTHWEST ---
    "Port of Spain": [10.6667, -61.5167],
    "Diego Martin": [10.7167, -61.5667],
    "Maraval": [10.6931, -61.5211],
    "Santa Cruz": [10.7000, -61.4667],
    "San Juan": [10.6455, -61.4489],
    "Barataria": [10.6522, -61.4622],
    "Carenage": [10.6833, -61.6000],
    "Blanchisseuse": [10.7933, -61.3094],

    # --- EAST-WEST CORRIDOR ---
    "St. Joseph": [10.6333, -61.4167],
    "St. Augustine": [10.6414, -61.4000],
    "Tunapuna": [10.6500, -61.3833],
    "Tacarigua": [10.6400, -61.3700],
    "Arouca": [10.6289, -61.3347],
    "Piarco": [10.6000, -61.3333],
    "Arima": [10.6333, -61.2833],
    "D'Abadie": [10.6333, -61.3000],

    # --- EAST / NORTHEAST ---
    "Sangre Grande": [10.5833, -61.1167],
    "Valencia": [10.6500, -61.2000],
    "Toco": [10.8333, -60.9500],
    "Matura": [10.6667, -61.0667],
    "Matelot": [10.8167, -61.1167],
    "Manzanilla": [10.5167, -61.0500],

    # --- CENTRAL ---
    "Chaguanas": [10.5167, -61.4000],
    "Couva": [10.4167, -61.4500],
    "Cunupia": [10.5333, -61.3833],
    "Freeport": [10.4500, -61.4167],
    "Tabaquite": [10.3833, -61.3000],
    "Talparo": [10.4667, -61.2667],
    "Montrose": [10.5100, -61.4100],

    # --- SOUTH / SOUTHWEST ---
    "San Fernando": [10.2833, -61.4667],
    "Princes Town": [10.2667, -61.3833],
    "Debe": [10.2167, -61.4444],
    "Penal": [10.1667, -61.4667],
    "Siparia": [10.1333, -61.5000],
    "Fyzabad": [10.1833, -61.5333],
    "Point Fortin": [10.1667, -61.6667],
    "La Brea": [10.2500, -61.6167],
    "Cedros": [10.0833, -61.8500],
    "Guayaguayare": [10.1333, -61.0500],
    "Mayaro": [10.3000, -61.0333],
    "Rio Claro": [10.3033, -61.1678],

    # --- TOBAGO ---
    "Scarborough (Tobago)": [11.1833, -60.7333],
    "Roxborough": [11.2333, -60.5833],
    "Charlotteville": [11.3167, -60.5500],
    "Speyside": [11.3000, -60.5333],
    "Canaan": [11.1500, -60.8167]
}

REPORT_FILE = "community_reports.csv"
COLUMNS = ["Timestamp", "Location", "Issue", "Description", "lat", "lon", "Color"]

# Ensure the file exists
if not os.path.exists(REPORT_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(REPORT_FILE, index=False)

# 3. WEATHER ENGINE
def get_live_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        res = requests.get(url).json()
        return res['current_weather']
    except:
        return None

# 4. NAVIGATION
st.sidebar.title("🇹🇹 T&T Climate Action")
page = st.sidebar.radio("Menu:", ["Live Map & Feed", "Report Incident (Pinpoint)", "Weather Station"])

# --- PAGE 1: LIVE MAP ---
if page == "Live Map & Feed":
    st.title("🗺️ Community Incident Map")
    df = pd.read_csv(REPORT_FILE)
    if not df.empty:
        st.map(df, latitude="lat", longitude="lon", color="Color", size=25)
        st.divider()
        st.subheader("📋 Recent Updates from the Ground")
        st.table(df.iloc[::-1].head(10)[["Timestamp", "Location", "Issue", "Description"]])
    else:
        st.info("No reports yet. Be the first to add an update!")

# --- PAGE 2: REPORT INCIDENT ---
elif page == "Report Incident (Pinpoint)":
    st.title("📢 Report an Issue")
    st.info("💡 Pro Tip: Click exactly where the issue is on the map for a precise GPS pin!")

    # Interactive Map for GPS Pinning
    m = folium.Map(location=[10.5, -61.3], zoom_start=9)
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=450, width=800)

    clicked_coords = None
    if map_data and map_data.get("last_clicked"):
        clicked_coords = map_data["last_clicked"]
        st.success(f"📍 GPS Captured: {clicked_coords['lat']:.4f}, {clicked_coords['lng']:.4f}")

    with st.form("incident_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            # Sort the list alphabetically so it's easier to find locations
            sorted_locs = sorted(list(LOCATION_MAP.keys()))
            rep_loc = st.selectbox("General Area / Constituency:", sorted_locs)
            rep_issue = st.selectbox("What's the issue?", ["Localized Flooding", "Excessive Heat", "Landslide", "Coastal Erosion", "Other"])
        with col2:
            rep_desc = st.text_area("Details (e.g. 'Street is underwater' or 'Crops dying')")
        
        submit = st.form_submit_button("Post Report to Map")

    if submit:
        # GPS Logic: Use the map click first; if they didn't click, use the dropdown town coords
        lat = clicked_coords['lat'] if clicked_coords else LOCATION_MAP[rep_loc][0]
        lon = clicked_coords['lng'] if clicked_coords else LOCATION_MAP[rep_loc][1]
        
        colors = {"Localized Flooding": "#0000FF", "Excessive Heat": "#FF0000", "Landslide": "#8B4513", "Coastal Erosion": "#008080", "Other": "#808080"}
        
        new_report = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Location": rep_loc if not clicked_coords else f"GPS: {rep_loc}",
            "Issue": rep_issue,
            "Description": rep_desc,
            "lat": lat, "lon": lon,
            "Color": colors.get(rep_issue, "#808080")
        }
        pd.DataFrame([new_report]).to_csv(REPORT_FILE, mode='a', header=False, index=False)
        st.success("Report submitted! View it on the Live Map page.")
        st.balloons()

# --- PAGE 3: WEATHER STATION ---
else:
    st.title("🌦️ Real-Time Climate Stations")
    st.write("Check the current heat and wind conditions across T&T.")
    
    selected_loc = st.selectbox("Choose a location to check:", sorted(list(LOCATION_MAP.keys())))
    coords = LOCATION_MAP[selected_loc]
    
    weather = get_live_weather(coords[0], coords[1])
    
    if weather:
        c1, c2, c3 = st.columns(3)
        c1.metric("Temperature", f"{weather['temperature']}°C")
        c2.metric("Wind Speed", f"{weather['windspeed']} km/h")
        c3.metric("Weather Code", f"{weather['weathercode']}")
        
        if weather['temperature'] > 31:
            st.error(f"🔥 High Heat Alert in {selected_loc}! Advise residents to stay indoors.")
    else:
        st.error("Data currently unavailable. Please check your internet.")