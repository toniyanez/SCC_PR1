import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# ----------------------------------------------------------------------------
# Heineken Digital Twin Streamlit App with Auto-Geocoding & Validation
# ----------------------------------------------------------------------------
# This app simulates the impact of trade tariffs and transport costs on Heineken's
# global margins relative to a user-defined baseline. It automatically fills missing
# geo-coordinates in nodes.csv and validates edge references.
# ----------------------------------------------------------------------------

# 1. App Configuration
st.set_page_config(page_title="Heineken Supply Chain Twin", layout="wide")
st.title("Heineken Digital Twin: Tariff & Transport Impact Simulator")

# 2. Load Data with Geocoding & Validation
@st.cache_data
def load_data():
    nodes = pd.read_csv("data/nodes.csv")  # cols: country, type, lat, lon
    edges = pd.read_csv("data/edges.csv")  # cols: origin, dest, transport_cost, tariff_rate

    # Geocode missing coordinates
    geolocator = Nominatim(user_agent="heineken_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)
    missing_mask = nodes[['lat', 'lon']].isna().any(axis=1)
    for idx in nodes[missing_mask].index:
        country = nodes.at[idx, 'country']
        loc = geocode(country)
        if loc:
            nodes.at[idx, 'lat'] = loc.latitude
            nodes.at[idx, 'lon'] = loc.longitude
        else:
            st.warning(f"Could not geocode country: {country}")

    # Validate that every edge origin/dest exists in nodes
    known_countries = set(nodes['country'])
    bad_origins = set(edges['origin']) - known_countries
    bad_dests = set(edges['dest']) - known_countries
    if bad_origins or bad_dests:
        errs = []
        if bad_origins:
            errs.append(f"Unknown origins: {bad_origins}")
        if bad_dests:
            errs.append(f"Unknown dests: {bad_dests}")
        st.error("Edge validation failed: " + "; ".join(errs))

    return nodes, edges

nodes, edges = load_data()

# 3. Sidebar Controls
st.sidebar.header("Simulation Settings")
baseline = st.sidebar.selectbox(
    "Select Baseline Scenario", ["Current", "No Tariffs", "Double Tariffs"]
)
transport_scale = st.sidebar.slider(
    "Transport Cost Multiplier", 0.5, 2.0, value=1.0, step=0.1
)

# 4. Compute Relative Margin Impact
edges_calc = edges.copy()
# transport cost scaling
edges_calc["adj_transport_cost"] = edges_calc["transport_cost"] * transport_scale
# tariff adjustment
if baseline == "Current":
    edges_calc["adj_tariff"] = edges_calc["tariff_rate"]
elif baseline == "No Tariffs":
    edges_calc["adj_tariff"] = 0
else:
    edges_calc["adj_tariff"] = edges_calc["tariff_rate"] * 2
# compute delta percentage vs. current
current_cost = edges_calc["transport_cost"] + edges_calc["tariff_rate"]
edges_calc["cost"] = edges_calc["adj_transport_cost"] + edges_calc["adj_tariff"]
edges_calc["delta_pct"] = (edges_calc["cost"] - current_cost) / current_cost * 100

# 5. Map Visualization
st.subheader("Global Supply Chain Map")
# node scatter layer
node_layer = pdk.Layer(
    "ScatterplotLayer",
    data=nodes,
    get_position='[lon, lat]',
    get_fill_color="[0, 128, 255]",  # uniform blue for simplicity
    get_radius=300000,
    pickable=True,
)
# edge arc layer
# precompute source/target positions using lookup dictionaries
country_to_coords = {row['country']:(row['lon'], row['lat']) for _, row in nodes.iterrows()}
edges_calc['source_lon'] = edges_calc['origin'].map(lambda c: country_to_coords.get(c, (None,None))[0])
edges_calc['source_lat'] = edges_calc['origin'].map(lambda c: country_to_coords.get(c, (None,None))[1])
edges_calc['target_lon'] = edges_calc['dest'].map(lambda c: country_to_coords.get(c, (None,None))[0])
edges_calc['target_lat'] = edges_calc['dest'].map(lambda c: country_to_coords.get(c, (None,None))[1])

edge_layer = pdk.Layer(
    "ArcLayer",
    data=edges_calc,
    get_source_position='[source_lon, source_lat]',
    get_target_position='[target_lon, target_lat]',
    get_width="np.clip(np.abs(delta_pct)/10, 1, 10)",
    get_source_color="[255 if delta_pct>0 else 0, 255 if delta_pct<0 else 0, 0]",
    get_target_color="[255 if delta_pct>0 else 0, 255 if delta_pct<0 else 0, 0]",
    pickable=True,
)

view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1)
deck = pdk.Deck(layers=[node_layer, edge_layer], initial_view_state=view_state)
st.pydeck_chart(deck)

# 6. Data Table & Metrics
st.subheader("Edge Cost Impact Details")
st.dataframe(edges_calc[['origin', 'dest', 'transport_cost', 'tariff_rate', 'cost', 'delta_pct']])

avg_delta = edges_calc['delta_pct'].mean()
st.metric(label="Average Cost Change (%)", value=f"{avg_delta:.2f}%")

# ----------------------------------------------------------------------------
# To run:
# pip install streamlit pandas numpy pydeck geopy
# streamlit run streamlit_app.py
# ----------------------------------------------------------------------------