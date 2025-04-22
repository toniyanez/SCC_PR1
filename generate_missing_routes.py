import pandas as pd
import json

# --- Configuration ---
outbound_path = 'data/outbound_routes.csv'
inbound_path  = 'data/routes_heineken.csv'
breweries_path = 'data/breweries.csv'
markets_path   = 'data/market_baseline_margins.csv'
scenarios_path = 'data/scenarios_heineken.json'

# Load existing data
outbound = pd.read_csv(outbound_path)
inbound  = pd.read_csv(inbound_path)
breweries = pd.read_csv(breweries_path)
markets   = pd.read_csv(markets_path)
with open(scenarios_path) as f:
    scenarios = json.load(f)

# Build location lookups
brew_locs = breweries.set_index('brewery_name')[['latitude','longitude']].to_dict('index')
market_locs = markets.set_index('country')[['latitude','longitude']].to_dict('index')

# Helper to skip generic
def valid_pair(orig, dest):
    return orig != 'Global' and dest != 'Global'

# Collect new outbound rows
new_out = []
for sc in scenarios:
    for orig in sc.get('route_origin', []):
        for dest in sc.get('route_destination', []):
            if not valid_pair(orig, dest): continue
            exists = ((outbound['origin_brewery'] == orig) & (outbound['destination_market'] == dest)).any()
            if exists: continue
            new_out.append({
                'route_id': f"AUTO_OUT_{orig}_{dest}",
                'product_id': 'P_HEINEKEN_330ML',
                'origin_brewery': orig,
                'destination_market': dest,
                'mode': 'Sea',
                'distance_km': None,
                'freight_cost_usd_total': None,
                'region': 'Global',
                'tariff_percent': None,
                'origin_latitude': brew_locs.get(orig, {}).get('latitude'),
                'origin_longitude': brew_locs.get(orig, {}).get('longitude'),
                'destination_latitude': market_locs.get(dest, {}).get('latitude'),
                'destination_longitude': market_locs.get(dest, {}).get('longitude')
            })

# Collect new inbound rows
new_in = []
for sc in scenarios:
    for orig in sc.get('route_origin', []):
        for dest in sc.get('route_destination', []):
            if not valid_pair(orig, dest): continue
            exists = ((inbound['origin_country'] == orig) & (inbound['destination_brewery'] == dest)).any()
            if exists: continue
            new_in.append({
                'route_id': f"AUTO_IN_{orig}_{dest}",
                'component_id': None,
                'origin_country': orig,
                'destination_brewery': dest,
                'mode': 'Sea',
                'distance_km': None,
                'freight_cost_usd_total': None,
                'region': 'Global',
                'tariff_percent': None,
                'origin_latitude': market_locs.get(orig, {}).get('latitude'),
                'origin_longitude': market_locs.get(orig, {}).get('longitude'),
                'destination_latitude': brew_locs.get(dest, {}).get('latitude'),
                'destination_longitude': brew_locs.get(dest, {}).get('longitude')
            })

# Append and save
if new_out:
    df_out = pd.DataFrame(new_out)
    outbound = pd.concat([outbound, df_out], ignore_index=True)
    outbound.to_csv(outbound_path, index=False)
    print(f"Added {len(new_out)} new outbound routes.")
else:
    print("No new outbound routes to add.")

if new_in:
    df_in = pd.DataFrame(new_in)
    inbound = pd.concat([inbound, df_in], ignore_index=True)
    inbound.to_csv(inbound_path, index=False)
    print(f"Added {len(new_in)} new inbound routes.")
else:
    print("No new inbound routes to add.")
