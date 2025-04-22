import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -- Load & cache your three CSVs --
@st.cache_data
def load_data():
    # component → manufacturing (inbound)
    inbound = pd.read_csv("data/routes_heineken.csv")
    # manufacturing → market (outbound)
    outbound = pd.read_csv("data/outbound_routes.csv")
    # brewery locations
    breweries = pd.read_csv("data/breweries.csv")
    return inbound, outbound, breweries

def main():
    st.set_page_config(page_title="Supply Chain Network Overview", layout="wide")
    st.title("🌐 Supply Chain Network Overview")

    inbound, outbound, breweries = load_data()

    # ----- KPI SUMMARY -----
    sup_pts = inbound.dropna(subset=['origin_latitude','origin_longitude'])[
        ['origin_latitude','origin_longitude']
    ].drop_duplicates()
    mkt_pts = outbound.dropna(subset=['destination_latitude','destination_longitude'])[
        ['destination_latitude','destination_longitude']
    ].drop_duplicates()

    col1, col2, col3 = st.columns(3)
    col1.metric("Suppliers", sup_pts.shape[0])
    col1.metric("Component Routes", inbound.shape[0])
    col2.metric("Manufacturers", breweries['brewery_name'].nunique())
    col2.metric("Final Routes", outbound.shape[0])
    col3.metric("Markets", mkt_pts.shape[0])

    # ----- GLOBAL MAP -----
    st.subheader("🌍 Global Supply Chain Map")
    fig = go.Figure()

    # 1️⃣ COMPONENT → MANUFACTURER (dashed red)
    inbound_clean = inbound.dropna(subset=[
        'origin_latitude','origin_longitude',
        'destination_latitude','destination_longitude'
    ])
    for i, r in inbound_clean.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r.origin_longitude, r.destination_longitude],
            lat=[r.origin_latitude,  r.destination_latitude],
            mode="lines",
            line=dict(color="red", dash="dash", width=1),
            name="Component Route",
            showlegend=(i == 0)
        ))

    # 2️⃣ MANUFACTURER → MARKET (solid green)
    outbound_clean = outbound.dropna(subset=[
        'origin_latitude','origin_longitude',
        'destination_latitude','destination_longitude'
    ])
    for i, r in outbound_clean.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r.origin_longitude, r.destination_longitude],
            lat=[r.origin_latitude,  r.destination_latitude],
            mode="lines",
            line=dict(color="green", width=2),
            name="Final Product Route",
            showlegend=(i == 0)
        ))

    # 3️⃣ SUPPLIERS as blue diamonds
    fig.add_trace(go.Scattergeo(
        lon=sup_pts.origin_longitude,
        lat=sup_pts.origin_latitude,
        mode="markers",
        marker=dict(symbol="diamond", size=8, color="blue"),
        name="Supplier"
    ))

    # 4️⃣ MANUFACTURERS as black squares
    fig.add_trace(go.Scattergeo(
        lon=breweries['longitude'],
        lat=breweries['latitude'],
        mode="markers",
        marker=dict(symbol="square", size=8, color="black"),
        name="Manufacturer"
    ))

    # 5️⃣ MARKETS as orange circles
    fig.add_trace(go.Scattergeo(
        lon=mkt_pts.destination_longitude,
        lat=mkt_pts.destination_latitude,
        mode="markers",
        marker=dict(symbol="circle", size=8, color="orange"),
        name="Market"
    ))

    fig.update_layout(
        title_text="Supply Chain: Components → Manufacturing → Market",
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="lightgray",
            showcountries=True
        ),
        legend=dict(title="Legend", orientation="v", x=0.85, y=0.90),
        margin=dict(l=0, r=0, t=40, b=0),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
