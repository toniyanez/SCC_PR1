import pandas as pd

# Fallback country centroids (approximate)
country_coords = {
    "USA": (37.0902, -95.7129),
    "UK": (55.3781, -3.4360),
    "Netherlands": (52.1326, 5.2913),
    "Germany": (51.1657, 10.4515),
    "France": (46.6034, 1.8883),
    "Nigeria": (9.0820, 8.6753),
    "Mexico": (23.6345, -102.5528),
    "China": (35.8617, 104.1954),
    "Vietnam": (14.0583, 108.2772),
    "Spain": (40.4637, -3.7492),
    "India": (20.5937, 78.9629),
    "Brazil": (-14.2350, -51.9253),
    "Italy": (41.8719, 12.5674),
    "Kenya": (-0.0236, 37.9062),
    "Ghana": (7.9465, -1.0232),
    "Singapore": (1.3521, 103.8198)
}

# Load the margins file
margins = pd.read_csv("data/market_baseline_margins.csv")

# Add lat/lon based on country name
margins['latitude'] = margins['country'].map(lambda x: country_coords.get(x, None)[0] if country_coords.get(x) else None)
margins['longitude'] = margins['country'].map(lambda x: country_coords.get(x, None)[1] if country_coords.get(x) else None)

# Save the enriched file
margins.to_csv("data/market_baseline_margins.csv", index=False)
print("✅ Updated market_baseline_margins.csv with coordinates.")
