import streamlit as st
import pandas as pd
import json
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_SCENARIO = os.getenv("DEFAULT_SCENARIO_ID", "S1")
PRICE_PER_UNIT = float(os.getenv("DEFAULT_PRICE_PER_UNIT", "1.00"))


PRICE_PER_UNIT = 1.00
from config import DEFAULT_SCENARIO_ID
scenario_selected = st.selectbox("Select Scenario", list(scenario_names.keys()), index=list(scenario_names).index(DEFAULT_SCENARIO_ID))

@st.cache_data
def load_data():
    routes = pd.read_csv("data/outbound_routes.csv")
    tariffs = pd.read_csv("data/tariffs_heineken.csv")
    margins = pd.read_csv("data/market_baseline_margins.csv")
    with open("data/scenarios_heineken.json") as f:
        scenarios = json.load(f)
    return routes, tariffs, margins, scenarios

def apply_scenario(routes, tariffs, scenario):
    def adjust_row(row):
        origin = row['origin_brewery'].split('_')[0]
        dest = row['destination_market']
        base_tariff = tariffs.query(
            f"origin_country == '{origin}' and destination_country == '{dest}' and hs_code == 2203.00.00"
        )['tariff_percent'].values[0] if not tariffs.empty else 0

        if scenario['sourcing_restrictions'] and origin in scenario['sourcing_restrictions']:
            row['blocked'] = True
            return row
        if (scenario['route_origin'] != ["Global"] and origin not in scenario['route_origin']):
            return row
        if (scenario['route_destination'] != ["Global"] and dest not in scenario['route_destination']):
            return row

        row['tariff_percent'] = base_tariff * scenario['tariff_multiplier']
        row['freight_cost_usd_total'] *= scenario['freight_multiplier']
        row['lead_time_days'] = scenario['lead_time_delay_days']
        return row

    routes = routes.copy()
    routes['blocked'] = False
    routes['lead_time_days'] = 0
    routes = routes.apply(adjust_row, axis=1)
    return routes

def calculate_margins(routes, margins):
    merged = routes.merge(margins, left_on='destination_market', right_on='country', how='left')
    merged['total_cost'] = merged['freight_cost_usd_total'] + (merged['tariff_percent'] / 100) * PRICE_PER_UNIT
    merged['new_margin'] = (PRICE_PER_UNIT - merged['total_cost']) / PRICE_PER_UNIT
    merged['margin_delta'] = merged['baseline_margin_percent']/100 - merged['new_margin']
    merged['revenue_loss_usd'] = merged['margin_delta'] * merged['average_volume_units_per_route'] * PRICE_PER_UNIT
    return merged[['route_id', 'origin_brewery', 'destination_market', 'new_margin', 'margin_delta', 'revenue_loss_usd', 'blocked', 'lead_time_days']]

def main():
    st.title("Heineken Supply Chain Scenario Simulator")
    routes, tariffs, margins, scenarios = load_data()

    scenario_names = {s['name']: s for s in scenarios}
    scenario_selected = st.selectbox("Select Scenario", list(scenario_names.keys()))
    scenario = scenario_names[scenario_selected]

    st.write("### Scenario Details")
    st.json(scenario)

    adjusted_routes = apply_scenario(routes, tariffs, scenario)
    result = calculate_margins(adjusted_routes, margins)

    st.write("### Simulation Results")
    st.dataframe(result.style.format({
        'new_margin': '{:.2%}',
        'margin_delta': '{:.2%}',
        'revenue_loss_usd': '${:,.0f}'
    }))

    total_loss = result['revenue_loss_usd'].sum()
    st.metric("Total Estimated Revenue Loss", f"${total_loss:,.0f}")

if __name__ == "__main__":
    main()
