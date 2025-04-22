import pandas as pd

# Load input route file and brewery/location lookups
routes = pd.read_csv("data/outbound_routes.csv")
breweries = pd.read_csv("data/breweries.csv")
markets = pd.read_csv("data/market_baseline_margins.csv")

# Clean duplicated columns if present
routes = routes.loc[:, ~routes.columns.duplicated()]
routes = routes.drop(columns=[col for col in routes.columns if ".1" in col or col.endswith(".1")], errors="ignore")

# Build lookup tables
brewery_lookup = breweries.set_index("brewery_name")[["latitude", "longitude"]].to_dict("index")
market_lookup = markets.set_index("country")[["latitude", "longitude"]].to_dict("index")

# Extract country tag from brewery ID (e.g., NL_ZOE → NL)
def extract_brewery_country(code):
    return code.split("_")[0] if "_" in code else code

routes["origin_country"] = routes["origin_brewery"].apply(extract_brewery_country)

# Enrich coordinates
routes["origin_latitude"] = routes["origin_brewery"].map(lambda b: brewery_lookup.get(b, {}).get("latitude"))
routes["origin_longitude"] = routes["origin_brewery"].map(lambda b: brewery_lookup.get(b, {}).get("longitude"))
routes["destination_latitude"] = routes["destination_market"].map(lambda m: market_lookup.get(m, {}).get("latitude"))
routes["destination_longitude"] = routes["destination_market"].map(lambda m: market_lookup.get(m, {}).get("longitude"))

# Drop intermediate fields
routes.drop(columns=["origin_country"], inplace=True)

# Save cleaned and enriched file
routes.to_csv("data/outbound_routes.csv", index=False)
print("✅ Fixed and updated: data/outbound_routes.csv")