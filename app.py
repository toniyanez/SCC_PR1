import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -- Data Loading ------------------------------------------------------------
@st.cache_data
def load_data():
    outbound  = pd.read_csv("data/outbound_routes.csv")
    inbound   = pd.read_csv("data/routes_heineken.csv")
    breweries = pd.read_csv("data/breweries.csv")
    return outbound, inbound, breweries

# -- Main -------------------------------------------------------------------
def main():
    st.set_page_config(layout="wide", page_title="Heineken Global Supply Chain")
    st.title("🍺 Heineken Global Supply Chain Map")

    # Load
    out_df, in_df, breweries = load_data()

    # Standardize lat/lon column names and drop bad rows
    for df in (out_df, in_df):
        df.rename(columns={
            "origin_latitude":      "olat",
            "origin_longitude":     "olon",
            "destination_latitude": "dlat",
            "destination_longitude":"dlon"
        }, inplace=True, errors="ignore")
        df.dropna(subset=["olat","olon","dlat","dlon"], inplace=True)

    # --- Network Summary Metrics ---------------------------------------------
    total_breweries = breweries.shape[0]
    total_suppliers = in_df.drop_duplicates(subset=["olat","olon"]).shape[0]
    total_routes    = len(in_df) + len(out_df)
    total_markets   = out_df["destination_market"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🏭 Breweries",    total_breweries)
    c2.metric("🔧 Suppliers",    total_suppliers)
    c3.metric("🚚 Total Routes", total_routes)
    c4.metric("🌐 Markets",      total_markets)

    st.markdown("---")

    # --- Build the Globe Map -------------------------------------------------
    fig = go.Figure()

    # Inbound (Components → Brewery) as dashed orange
    for _, r in in_df.iterrows():
        origin = r.get("origin_country", "?")
        dest   = r.get("destination_brewery", "?")
        tariff = r.get("tariff_percent", 0)
        fig.add_trace(go.Scattergeo(
            lon=[r["olon"], r["dlon"]],
            lat=[r["olat"], r["dlat"]],
            mode="lines",
            line=dict(color="orange", dash="dash", width=2),
            name=f"{origin} → {dest} ({tariff:.0f}% tariff)",
            hoverinfo="text",
            hovertext=f"{origin} → {dest}\nTariff: {tariff:.0f}%"
        ))

    # Outbound (Brewery → Market) as solid green
    for _, r in out_df.iterrows():
        origin = r.get("origin_brewery", "?")
        dest   = r.get("destination_market", "?")
        tariff = r.get("tariff_percent", 0)
        fig.add_trace(go.Scattergeo(
            lon=[r["olon"], r["dlon"]],
            lat=[r["olat"], r["dlat"]],
            mode="lines",
            line=dict(color="green", width=2),
            name=f"{origin} → {dest} ({tariff:.0f}% tariff)",
            hoverinfo="text",
            hovertext=f"{origin} → {dest}\nTariff: {tariff:.0f}%"
        ))

    # Brewery sites (black squares)
    fig.add_trace(go.Scattergeo(
        lon=breweries["longitude"],
        lat=breweries["latitude"],
        mode="markers+text",
        marker=dict(symbol="square", size=8, color="black"),
        text=breweries["brewery_name"],
        textposition="top center",
        name="Brewery"
    ))

    # Supplier sites (blue diamonds) from inbound origins
    suppliers = in_df[["olon","olat"]].drop_duplicates()
    fig.add_trace(go.Scattergeo(
        lon=suppliers["olon"],
        lat=suppliers["olat"],
        mode="markers",
        marker=dict(symbol="diamond", size=8, color="blue"),
        name="Supplier"
    ))

    # --- Layout --------------------------------------------------------------
    fig.update_layout(
        title_text="Heineken Supply Chain: Components → Breweries → Markets",
        showlegend=True,
        legend=dict(
            x=1.02, y=0.5, traceorder="normal",
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.8)"
        ),
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="lightgray",
            coastlinecolor="gray"
        ),
        margin=dict(l=0, r=250, t=50, b=0),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
