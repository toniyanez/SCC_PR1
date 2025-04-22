import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# Heineken Supply Chain Map w/ Clickable Route Legend
# -----------------------------------------------------------------------------

# 1. Page config
st.set_page_config(page_title="Heineken Supply Chain Network", layout="wide")
st.title("Heineken Global Supply Chain Map")

# 2. Load data
nodes = pd.read_csv("data/nodes.csv")
edges = pd.read_csv("data/edges.csv")

# 3. Merge coords into edges
nc = nodes.dropna(subset=["lat","lon"]).copy()
edges = (
    edges
    .merge(nc[["country","lat","lon"]], left_on="origin", right_on="country")
    .rename(columns={"lat":"src_lat","lon":"src_lon"}).drop(columns="country")
    .merge(nc[["country","lat","lon"]], left_on="dest", right_on="country")
    .rename(columns={"lat":"dst_lat","lon":"dst_lon"}).drop(columns="country")
)

# 4. Build human‐readable labels and styling
def tone_color(rate):
    if rate > 0.10: return "red"
    elif rate > 0.05: return "gold"
    else:            return "green"

edges["color"] = edges["tariff_rate"].apply(tone_color)
edges["width"] = edges["tariff_rate"] * 5 + 1
edges["label"] = edges.apply(
    lambda r: f"{r.origin} → {r.dest} ({int(r.tariff_rate*100)}% tariff)",
    axis=1
)

type_color = {"manufacturer":"blue","supplier":"teal","market":"crimson"}
nc["marker_color"] = nc["type"].map(type_color)

# 5. Initialize Plotly figure
fig = go.Figure()

# 5a. World basemap
fig.update_geos(
    showcountries=True, countrycolor="black",
    showland=True, landcolor="lightgray",
    projection_type="equirectangular"
)

# 5b. Add each route as its own legend‑entry trace
for _, r in edges.iterrows():
    fig.add_trace(go.Scattergeo(
        lon=[r.src_lon, r.dst_lon],
        lat=[r.src_lat, r.dst_lat],
        mode="lines",
        line=dict(width=r.width, color=r.color),
        hoverinfo="none",
        name=r.label,     # each route appears in legend
        showlegend=True
    ))

# 5c. Add site nodes (no legend entries)
fig.add_trace(go.Scattergeo(
    lon=nc["lon"],
    lat=nc["lat"],
    mode="markers",
    marker=dict(size=8, color=nc["marker_color"], line=dict(width=1, color="black")),
    text=nc["country"],
    hoverinfo="text",
    showlegend=False
))

fig.update_layout(
    margin=dict(l=0,r=0,t=0,b=0),
    legend=dict(
        title="Routes (click to toggle)",
        itemsizing="constant",
        font=dict(size=10),
        x=0.85, y=0.5,    # position on right
        bgcolor="rgba(255,255,255,0.8)"
    )
)

# 6. Render
st.plotly_chart(fig, use_container_width=True)

# 7. Site Legend in sidebar
st.sidebar.markdown("**Site Legend**")
for tp, col in type_color.items():
    bullet = f"<span style='display:inline-block;width:12px;height:12px;background:{col};margin-right:8px;'></span>"
    st.sidebar.markdown(bullet + tp.capitalize(), unsafe_allow_html=True)
