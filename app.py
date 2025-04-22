import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from config import DEFAULT_SCENARIO_ID, PRICE_PER_UNIT

# Load data
@st.cache_data
def load_data():
    routes = pd.read_csv("data/outbound_routes.csv")
    tariffs = pd.read_csv("data/tariffs_heineken.csv")
    margins = pd.read_csv("data/market_baseline_margins.csv")
    breweries = pd.read_csv("data/breweries.csv")
    inbound = pd.read_csv("data/routes_heineken.csv")

    # Filter valid coords
    routes = routes.dropna(subset=['origin_latitude','origin_longitude','destination_latitude','destination_longitude'])
    inbound = inbound.dropna(subset=['origin_latitude','origin_longitude','destination_latitude','destination_longitude'])

    with open("data/scenarios_heineken.json") as f:
        scenarios = json.load(f)
    return routes, tariffs, margins, breweries, inbound, scenarios


def apply_scenario(routes, tariffs, scenario):
    def adjust_row(row):
        origin = row['origin_brewery'].split('_')[0]
        dest = row.get('destination_market', row.get('destination_brewery','')).split('_')[0]
        q = f"origin_country == '{origin}' and destination_country == '{dest}' and hs_code == '2203.00.00'"
        match = tariffs.query(q)
        base_tariff = match['tariff_percent'].iat[0] if not match.empty else 0
        if scenario.get('sourcing_restrictions') and origin in scenario['sourcing_restrictions']:
            row['blocked'] = True
            return row
        row['tariff_percent'] = base_tariff * scenario.get('tariff_multiplier',1)
        row['freight_cost_usd_total'] *= scenario.get('freight_multiplier',1)
        row['lead_time_days'] = scenario.get('lead_time_delay_days',0)
        return row
    df = routes.copy()
    df['blocked'] = False
    df['lead_time_days'] = 0
    return df.apply(adjust_row,axis=1)


def calculate_margins(df, margins):
    m = df.merge(margins, left_on='destination_market', right_on='country', how='left')
    m['total_cost'] = m['freight_cost_usd_total'] + (m['tariff_percent']/100)*PRICE_PER_UNIT
    m['new_margin'] = ((PRICE_PER_UNIT - m['total_cost'])/PRICE_PER_UNIT).clip(-1,1)
    m['margin_delta'] = (m['baseline_margin_percent']/100 - m['new_margin']).clip(-1,1)
    m['revenue_loss_usd'] = m['margin_delta'] * m['average_volume_units_per_route'] * PRICE_PER_UNIT
    return m


def show_dashboard(df):
    st.subheader("📊 KPI Summary")
    st.metric("Total Revenue Loss", f"${df['revenue_loss_usd'].sum():,.0f}")
    st.metric("Blocked Routes", int(df['blocked'].sum()))
    st.metric("Average Margin Drop", f"{df['margin_delta'].mean()*100:.2f}%")
    st.subheader("📉 Margin Impact by Market")
    st.bar_chart(df.set_index('destination_market')['margin_delta'])


def show_map(breweries, inbound):
    st.subheader("🌍 Global Supplier & Brewery Locations")
    fig = go.Figure()
    # Manufacturer sites
    fig.add_trace(go.Scattergeo(
        lon=breweries['longitude'], lat=breweries['latitude'],
        mode='markers+text', text=breweries['brewery_name'], marker=dict(symbol='circle',size=8,color='green'),
        textposition='top center', name='Brewery'
    ))
    # Supplier origins
    suppliers = inbound[['origin_latitude','origin_longitude','origin_country']].drop_duplicates()
    fig.add_trace(go.Scattergeo(
        lon=suppliers['origin_longitude'], lat=suppliers['origin_latitude'],
        mode='markers+text', text=suppliers['origin_country'], marker=dict(symbol='diamond',size=8,color='blue'),
        textposition='bottom center', name='Supplier'
    ))
    fig.update_layout(geo=dict(projection_type='natural earth',showland=True,landcolor='lightgray'),height=600,title='Heineken Global Nodes')
    st.plotly_chart(fig,use_container_width=True)


def show_routes_map(outbound, inbound):
    st.subheader("🚛 Global Route Network Map with Tariffs")
    fig = go.Figure()
    # Prepare
    out = outbound.rename(columns={'origin_latitude':'o_lat','origin_longitude':'o_lon','destination_latitude':'d_lat','destination_longitude':'d_lon'})
    inb = inbound.rename(columns={'origin_latitude':'o_lat','origin_longitude':'o_lon','destination_latitude':'d_lat','destination_longitude':'d_lon'})
    # Outbound
    for _, r in out.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r['o_lon'],r['d_lon']], lat=[r['o_lat'],r['d_lat']], mode='lines',
            line=dict(width=1.5,color='green'),opacity=0.7, name='Outbound'
        ))
        # tariff label midpoint
        mid_lon, mid_lat = (r['o_lon']+r['d_lon'])/2,(r['o_lat']+r['d_lat'])/2
        fig.add_trace(go.Scattergeo(lon=[mid_lon],lat=[mid_lat],mode='text',text=f"{r['tariff_percent']:.1f}%",
            textfont=dict(color='darkgreen',size=10),showlegend=False))
    # Inbound
    for _, r in inb.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r['o_lon'],r['d_lon']], lat=[r['o_lat'],r['d_lat']], mode='lines',
            line=dict(width=1,color='blue'),opacity=0.5, name='Inbound'
        ))
        mid_lon, mid_lat = (r['o_lon']+r['d_lon'])/2,(r['o_lat']+r['d_lat'])/2
        fig.add_trace(go.Scattergeo(lon=[mid_lon],lat=[mid_lat],mode='text',text=f"{r['tariff_percent']:.1f}%",
            textfont=dict(color='darkblue',size=10),showlegend=False))
    fig.update_layout(title='Supply Chain Routes with Tariff Labels',showlegend=False,
                      geo=dict(projection_type='natural earth',showland=True,landcolor='lightgray'))
    st.plotly_chart(fig,use_container_width=True)


def main():
    st.set_page_config(page_title="Heineken Digital Twin",layout="wide")
    st.title("🍺 Heineken Digital Supply Chain Twin")
    routes, tariffs, margins, breweries, inbound, scenarios = load_data()
    names={s['name']:s for s in scenarios}
    default=scenarios[0]['name']
    sel=st.sidebar.selectbox("Select Scenario",list(names.keys()),index=list(names.keys()).index(default))
    scenario=names[sel]
    st.sidebar.markdown("---")
    st.sidebar.json(scenario)
    adjusted=apply_scenario(routes,tariffs,scenario)
    results=calculate_margins(adjusted,margins)
    tab1,tab2,tab3,tab4=st.tabs(["📊 Dashboard","🌍 Map","🚛 Routes","📄 Data"])
    with tab1: show_dashboard(results)
    with tab2: show_map(breweries,inbound)
    with tab3: show_routes_map(adjusted,inbound)
    with tab4:
        st.dataframe(results)
        st.download_button("Download CSV",data=results.to_csv(index=False),file_name="output.csv")

if __name__=="__main__":
    main()
