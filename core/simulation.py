import pandas as pd
import json

PRICE_PER_UNIT = 1.00  # USD (example)

def load_data():
    routes = pd.read_csv("outbound_routes.csv")
    tariffs = pd.read_csv("tariffs_heineken.csv")
    margins = pd.read_csv("market_baseline_margins.csv")
    with open("scenarios_heineken.json") as f:
        scenarios = json.load(f)
    return routes, tariffs, margins, scenarios

def apply_scenario(routes, tariffs, scenario):
    def adjust_row(row):
        origin = row['origin_brewery'].split('_')[0]  # NL_ZOE → NL
        dest = row['destination_market']
        region = row['region']
        base_tariff = tariffs.query(
            f"origin_country == '{origin}' and destination_country == '{dest}' and hs_code == 2203.00.00"
        )['tariff_percent'].values[0] if not tariffs.empty else 0

        # Scenario filters
        if scenario['sourcing_restrictions'] and origin in scenario['sourcing_restrictions']:
            row['blocked'] = True
            return row
        if (scenario['route_origin'] != ["Global"] and origin not in scenario['route_origin']):
            return row
        if (scenario['route_destination'] != ["Global"] and dest not in scenario['route_destination']):
            return row

        # Apply scenario effects
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
    merged['revenue_loss_per_unit'] = merged['margin_delta'] * PRICE_PER_UNIT
    return merged[['route_id', 'destination_market', 'tariff_percent', 'freight_cost_usd_total', 'new_margin', 'margin_delta', 'revenue_loss_per_unit', 'blocked', 'lead_time_days']]

def main(scenario_id):
    routes, tariffs, margins, scenarios = load_data()
    scenario = next(s for s in scenarios if s['id'] == scenario_id)
    adjusted = apply_scenario(routes, tariffs, scenario)
    result = calculate_margins(adjusted, margins)
    print(result)

if __name__ == "__main__":
    main("S3")  # Test with scenario Red Sea Disruption
