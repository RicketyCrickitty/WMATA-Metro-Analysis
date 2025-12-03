#!/usr/bin/env python3
"""
Fixed & improved version of rail_suggestion_by_bus.py

Improvements:
- Robust column detection for multiple rail CSV formats.
- Safer aggregation and sanity checks of rail boardings.
- Uses station_mappings if available; otherwise attempts careful fuzzy name matching
  between rail station names and bus stop names (requires reasonably close matches).
- Better bus hotspot clustering: rounding to 4 decimal places (~11 m) rather than 3.
- Clear, informative logging and safer thresholds.
- No sklearn dependency (keeps portability).
- Outputs folium map 'proposal_map.html' and prints top candidates.

Usage:
    python rail_suggestion_by_bus_fixed.py
"""

import os
import sys
import math
import traceback
import pandas as pd
import folium
from difflib import SequenceMatcher

# --- Configuration ---
RAIL_FILES = [
    'Metro_Rail_Ridership_Dataset_Summary_CYTD2025.csv',
    'Metro_Rail_Ridership_Dataset_Summary_CY2024.csv',
    'Metro_Rail_Ridership_Dataset_Summary_CY2023.csv',
    'Metro_Rail_Ridership_Dataset_Summary_CY2022.csv'
]
BUS_FILE = 'BusRdr_Routes_Stops_Time_Periods.csv'
OUTPUT_MAP = 'proposal_map.html'

# Thresholds (tune as needed)
HOTSPOT_MIN_BOARDINGS = 100     # min aggregated boardings for a hotspot to be considered
CANDIDATE_MIN_BOARDINGS = 500   # bus boardings threshold to be a candidate
MIN_DISTANCE_MILES = 1.0        # min distance from nearest rail to be considered a gap
HOTSPOT_ROUND_DECIMALS = 4     # 4 decimals ~ 11 meters (safer clustering than 3 decimals)

# Try to import station_mappings mapping if provided. It's optional.
STATION_ID_TO_NAME = None
try:
    from station_mappings import STATION_ID_TO_NAME as _MAP
    STATION_ID_TO_NAME = _MAP
    print("Loaded station_mappings.STATION_ID_TO_NAME")
except Exception:
    print("No station_mappings import available or failed to import. Will attempt fuzzy name matching instead.")


# -------------------------
# Utility helper functions
# -------------------------
def haversine_miles(lon1, lat1, lon2, lat2):
    """Return distance in miles between two decimal degree coordinates."""
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2.0)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2.0)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 3956  # Radius of Earth in miles
    return c * r


def similar(a, b):
    """Return a similarity ratio 0..1 between two strings (case-insensitive)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_best_column(df_cols, candidates):
    """
    Given df.columns and a list of candidate names (ordered), return the first matching column name present in df.
    Matching is case-insensitive, underscores/spaces ignored.
    """
    normalized = {c: c for c in df_cols}
    norm_map = {}
    for c in df_cols:
        key = c.strip().lower().replace(' ', '').replace('-', '').replace('_', '')
        norm_map[key] = c

    for cand in candidates:
        cand_key = cand.strip().lower().replace(' ', '').replace('-', '').replace('_', '')
        if cand_key in norm_map:
            return norm_map[cand_key]
    # fallback: try contains
    for cand in candidates:
        for c in df_cols:
            if cand.lower() in c.lower():
                return c
    return None


# -------------------------
# Main analysis function
# -------------------------
def run_analysis():
    print("=== START: Rail/Bus gap analysis ===\n")

    # -------------------------
    # 1) Load & process rail datasets
    # -------------------------
    print("1) Loading rail datasets...")
    year_station_dfs = []
    found_any_rail = False

    for f in RAIL_FILES:
        if not os.path.isfile(f):
            print(f" - Skipping (not found): {f}")
            continue

        try:
            df = pd.read_csv(f)
            found_any_rail = True
        except Exception as e:
            print(f" - Failed to read {f}: {e}")
            continue

        # normalize column names for easier matching
        df_cols = list(df.columns)
        # Pick probable date column
        date_col = find_best_column(df_cols, ['svc_date', 'svcdate', 'date', 'service_date', 'day'])
        # Pick probable stop/station id column
        stop_col = find_best_column(df_cols, ['stop_id', 'stopid', 'station_id', 'stationid', 'stop'])
        # Pick probable boardings column
        board_col = find_best_column(df_cols, [
            'avg_boardings', 'avg_boarding', 'avg_daily_boardings', 'boardings', 'daily_boardings', 'avg_daily'
        ])

        print(f" - File: {f}")
        print(f"   Columns found -> date: {date_col}, stop: {stop_col}, boardings: {board_col}")

        if not stop_col or not board_col:
            print(f"   Skipping {f}: missing required columns (stop or boardings).")
            continue

        # Ensure data types
        # Convert date col to datetime if possible; if not present, create a synthetic date grouping
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            except Exception:
                df[date_col] = pd.to_datetime(df[date_col].astype(str), errors='coerce')
        else:
            # Make a synthetic date column so grouping works (all rows same date)
            df['_synthetic_date_'] = pd.NaT
            date_col = '_synthetic_date_'

        # Drop rows where boardings is missing or stop id missing
        df = df.dropna(subset=[board_col, stop_col])

        # If boardings are strings with commas, remove commas
        if df[board_col].dtype == object:
            # Attempt numeric conversion
            df[board_col] = df[board_col].astype(str).str.replace(',', '').astype(float, errors='ignore')

        # Aggregate to daily totals per stop
        # If date_col is synthetic (all NaT), group by whatever unique index grouping is available
        try:
            daily = df.groupby([date_col, stop_col])[board_col].sum().reset_index()
            # Now compute per-stop mean of daily totals (gives typical daily boardings for that year)
            station_avg = daily.groupby(stop_col)[board_col].mean().reset_index()
            station_avg.columns = [stop_col, 'avg_daily_boardings_for_year']
            station_avg['source_file'] = f
            year_station_dfs.append(station_avg)
            print(f"   Processed: {len(station_avg)} stations (year summary).")
        except Exception as e:
            print(f"   Error aggregating {f}: {e}\n{traceback.format_exc()}")

    if not found_any_rail or not year_station_dfs:
        print("\nError: No usable rail data found. Aborting.")
        return

    # Combine years: compute multi-year mean per stop id
    all_years = pd.concat(year_station_dfs, ignore_index=True)
    rail_usage = all_years.groupby(all_years.columns[0])['avg_daily_boardings_for_year'].mean().reset_index()
    rail_usage.columns = ['STOP_ID', 'AVG_BOARDINGS']
    print(f"\nCombined rail dataset: {len(rail_usage)} unique STOP_ID entries (multi-year average).")

    # Try to map STOP_ID to STATION_NAME using station_mappings if present
    if STATION_ID_TO_NAME:
        rail_usage['STATION_NAME'] = rail_usage['STOP_ID'].map(STATION_ID_TO_NAME)
        # drop those without mapping
        mapped_count = rail_usage['STATION_NAME'].notna().sum()
        print(f" - Mapped {mapped_count} stations using station_mappings.")
        rail_usage = rail_usage.dropna(subset=['STATION_NAME'])
    else:
        # If no station mapping available, attempt to use STOP_ID as name if it looks like text
        rail_usage['STATION_NAME'] = rail_usage['STOP_ID'].astype(str)
        print(" - station_mappings not available; using STOP_ID as station name (may be numeric).")

    # Show top sample
    print("\nTop rail stations by AVG_BOARDINGS (sample):")
    print(rail_usage.sort_values('AVG_BOARDINGS', ascending=False).head(5).to_string(index=False))

    # -------------------------
    # 2) Load bus data
    # -------------------------
    print("\n2) Loading bus dataset...")
    if not os.path.isfile(BUS_FILE):
        print(f"Error: Bus file '{BUS_FILE}' not found. Aborting.")
        return

    try:
        bus_df = pd.read_csv(BUS_FILE)
    except Exception as e:
        print(f"Error reading bus file: {e}\n{traceback.format_exc()}")
        return

    # Ensure necessary columns exist (case-insensitive)
    bus_cols = list(bus_df.columns)
    # Standardize some expected names
    stop_col_bus = find_best_column(bus_cols, ['stop', 'stop_name', 'stoplabel'])
    lat_col = find_best_column(bus_cols, ['lat', 'latitude'])
    lon_col = find_best_column(bus_cols, ['lon', 'lng', 'longitude', 'long'])
    sum_on_col = find_best_column(bus_cols, ['sum_passengers_on', 'sum_on', 'passengers_on', 'sum_boardings', 'sum_passengers'])

    if not stop_col_bus or not lat_col or not lon_col or not sum_on_col:
        print("Warning: bus dataset missing one of required columns (STOP/LAT/LON/SUM_PASSENGERS_ON).")
        print(f"Detected columns: stop={stop_col_bus}, lat={lat_col}, lon={lon_col}, sum_on={sum_on_col}")
        # attempt to continue with best guesses
    else:
        # rename for convenience
        bus_df = bus_df.rename(columns={
            stop_col_bus: 'STOP',
            lat_col: 'LAT',
            lon_col: 'LON',
            sum_on_col: 'SUM_PASSENGERS_ON'
        })

    # Clean types
    bus_df = bus_df.dropna(subset=['LAT', 'LON'])
    try:
        bus_df['LAT'] = pd.to_numeric(bus_df['LAT'], errors='coerce')
        bus_df['LON'] = pd.to_numeric(bus_df['LON'], errors='coerce')
        bus_df = bus_df.dropna(subset=['LAT', 'LON'])
    except Exception:
        pass

    print(f" - Loaded bus data rows: {len(bus_df)}")

    # -------------------------
    # 3) Infer rail station coordinates
    # -------------------------
    print("\n3) Inferring rail station coordinates...")

    rail_locations = []

    # If station_mappings provided and contains coordinates, prefer that.
    if STATION_ID_TO_NAME and isinstance(STATION_ID_TO_NAME, dict):
        # If mapping keys are IDs (stop ids) to names; but we need coordinates — check if mapping includes lat/lon
        # Many station_mappings provide names only. We can attempt fuzzy matching between station names and bus stops.
        print(" - station_mappings present. Attempting to infer coordinates via bus stop matching (fuzzy).")
    else:
        print(" - station_mappings not present. Using fuzzy name matching between station names and bus stop names.")

    # Build bus stop name -> aggregated coordinates map (to speed fuzzy matching)
    # Use grouping by exact stop names producing mean LAT/LON and aggregated SUM_PASSENGERS_ON
    bus_stop_agg = bus_df.groupby('STOP').agg({
        'LAT': 'mean',
        'LON': 'mean',
        'SUM_PASSENGERS_ON': 'sum'
    }).reset_index()

    # For faster search, create list of bus stop names
    bus_stop_names = bus_stop_agg['STOP'].astype(str).tolist()

    # If STATION_ID_TO_NAME present: iterate rail_usage rows and try to map
    for _, row in rail_usage.iterrows():
        stop_id = row['STOP_ID']
        station_name = row['STATION_NAME'] if pd.notna(row['STATION_NAME']) else str(stop_id)

        best_match = None
        best_ratio = 0.0
        best_lat = None
        best_lon = None

        # First try the simple substring match (word boundary) but case-insensitive
        # This avoids false positives from partial short words.
        station_tokens = [t for t in ''.join(ch if ch.isalnum() else ' ' for ch in str(station_name)).split() if len(t) > 1]

        # Search through bus_stop_names
        for i, bname in enumerate(bus_stop_names):
            if not bname or not isinstance(bname, str):
                continue
            # quick token overlap check
            b_tokens = [t for t in ''.join(ch if ch.isalnum() else ' ' for ch in bname).split() if len(t) > 1]
            token_overlap = len(set(t.lower() for t in station_tokens) & set(t.lower() for t in b_tokens))
            ratio = similar(station_name, bname)

            # prefer token overlap OR high similarity
            if token_overlap >= 1 and ratio > 0.6:
                # candidate
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = bname
            elif ratio > best_ratio and ratio > 0.78:
                # high similarity even without token overlap
                best_ratio = ratio
                best_match = bname

        if best_match:
            # grab coordinates from bus_stop_agg
            match_row = bus_stop_agg[bus_stop_agg['STOP'] == best_match].iloc[0]
            best_lat = float(match_row['LAT'])
            best_lon = float(match_row['LON'])
            rail_locations.append({
                'STOP_ID': stop_id,
                'STATION_NAME': station_name,
                'RAIL_BOARDINGS': float(row['AVG_BOARDINGS']),
                'LAT': best_lat,
                'LON': best_lon,
                'MATCHED_STOP': best_match,
                'MATCH_SCORE': best_ratio
            })
        else:
            # no reasonable match found — skip for now
            # (We avoid guessing coordinates from other heuristics to prevent false placements)
            continue

    rail_loc_df = pd.DataFrame(rail_locations)
    print(f" - Located coordinates for {len(rail_loc_df)} rail stations via bus stop fuzzy matching.")

    # Show some of the matched stations
    if not rail_loc_df.empty:
        print("\nSample matched rail stations (name -> matched bus stop -> score):")
        print(rail_loc_df[['STATION_NAME', 'MATCHED_STOP', 'MATCH_SCORE']].sort_values('MATCH_SCORE', ascending=False).head(8).to_string(index=False))

    # -------------------------
    # 4) Identify bus hotspots (improved clustering)
    # -------------------------
    print("\n4) Identifying bus hotspots (improved clustering by rounding to 4 decimals)...")
    # Round lat/lon to cluster very nearby stops, but with higher precision than before.
    bus_df['LAT_R'] = bus_df['LAT'].round(HOTSPOT_ROUND_DECIMALS)
    bus_df['LON_R'] = bus_df['LON'].round(HOTSPOT_ROUND_DECIMALS)

    agg = bus_df.groupby(['LAT_R', 'LON_R']).agg({
        'SUM_PASSENGERS_ON': 'sum',
        'STOP': lambda x: x.mode().iat[0] if not x.mode().empty else x.iloc[0],
        'ROUTE_NAME': lambda x: ', '.join(pd.unique(x.astype(str))[:5])
    }).reset_index()

    # Filter to hotspots with meaningful boardings
    bus_hotspots = agg[agg['SUM_PASSENGERS_ON'] >= HOTSPOT_MIN_BOARDINGS].copy()
    bus_hotspots = bus_hotspots.rename(columns={'STOP': 'REP_STOP', 'ROUTE_NAME': 'ROUTES'})

    print(f" - Found {len(bus_hotspots)} bus hotspots with SUM_PASSENGERS_ON >= {HOTSPOT_MIN_BOARDINGS}.")

    # -------------------------
    # 5) Gap analysis: find hotspots far from existing rail
    # -------------------------
    print("\n5) Performing gap analysis...")
    potential_stations = []
    for _, b in bus_hotspots.iterrows():
        b_lat = float(b['LAT_R'])
        b_lon = float(b['LON_R'])
        b_board = float(b['SUM_PASSENGERS_ON'])

        # find nearest rail station (from rail_loc_df)
        min_dist = float('inf')
        nearest_station = None
        for _, r in rail_loc_df.iterrows():
            try:
                d = haversine_miles(b_lon, b_lat, float(r['LON']), float(r['LAT']))
            except Exception:
                continue
            if d < min_dist:
                min_dist = d
                nearest_station = r['STATION_NAME']

        # Candidate criteria
        if b_board >= CANDIDATE_MIN_BOARDINGS and (min_dist is None or min_dist > MIN_DISTANCE_MILES):
            potential_stations.append({
                'Name': b['REP_STOP'],
                'Lat': b_lat,
                'Lon': b_lon,
                'Bus_Boardings': b_board,
                'Nearest_Rail': nearest_station if nearest_station is not None else "None",
                'Distance_Miles': round(min_dist, 2) if min_dist != float('inf') else None,
                'Routes': b['ROUTES']
            })

    potential_df = pd.DataFrame(potential_stations)
    if potential_df.empty:
        print(" - No high-confidence candidates found with current thresholds.")
    else:
        potential_df = potential_df.sort_values('Bus_Boardings', ascending=False).head(50)
        print(f" - {len(potential_df)} candidate hotspot(s) pass the thresholds (showing top 50).")

    # -------------------------
    # 6) Generate Map
    # -------------------------
    print("\n6) Generating folium map...")

    # Default map center - center on Washington DC if data in that area
    center_lat, center_lon = 38.8951, -77.0364
    try:
        # attempt to center map on mean of bus hotspots for better view
        if not bus_hotspots.empty:
            center_lat = float(bus_hotspots['LAT_R'].mean())
            center_lon = float(bus_hotspots['LON_R'].mean())
    except Exception:
        pass

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='cartodbpositron')

    # Feature groups for toggles
    rail_fg = folium.FeatureGroup(name='Existing Rail (dots)', show=True)
    rail_labels_fg = folium.FeatureGroup(name='Rail Labels (toggle)', show=False)
    proposed_fg = folium.FeatureGroup(name='Proposed Stations (dots)', show=True)
    proposed_labels_fg = folium.FeatureGroup(name='Proposed Labels (toggle)', show=False)
    hotspot_fg = folium.FeatureGroup(name='Bus Hotspots', show=False)

    # Plot rail stations (from rail_loc_df)
    for _, r in rail_loc_df.iterrows():
        lat = float(r['LAT'])
        lon = float(r['LON'])
        popup_html = f"<b>{r['STATION_NAME']}</b><br>Avg Daily Boardings (multi-year): {int(r['RAIL_BOARDINGS']):,}"
        folium.CircleMarker(location=[lat, lon], radius=4, color='blue', fill=True, fill_color='#3186cc',
                            popup=popup_html).add_to(rail_fg)
        # label as a tooltip inside labels FG
        folium.CircleMarker(location=[lat, lon], radius=0.1, opacity=0,
                            tooltip=folium.Tooltip(r['STATION_NAME'], permanent=True, direction='right')
                            ).add_to(rail_labels_fg)

    # Plot bus hotspots
    for _, h in bus_hotspots.iterrows():
        folium.CircleMarker(location=[float(h['LAT_R']), float(h['LON_R'])], radius=3, color='orange', fill=True,
                            fill_opacity=0.8, popup=f"{h['REP_STOP']}<br>Boardings: {int(h['SUM_PASSENGERS_ON']):,}"
                            ).add_to(hotspot_fg)

    # Plot proposed stations
    for _, p in potential_df.iterrows():
        folium.Marker(location=[p['Lat'], p['Lon']],
                      icon=folium.Icon(color='red', icon='bus', prefix='fa'),
                      popup=f"<b>PROPOSED: {p['Name']}</b><br>Bus Boardings: {int(p['Bus_Boardings']):,}<br>Nearest Rail: {p['Nearest_Rail']} ({p['Distance_Miles']} mi)"
                      ).add_to(proposed_fg)

        folium.Circle(location=[p['Lat'], p['Lon']], radius=800, color='red', weight=1, fill=True,
                      fill_opacity=0.08).add_to(proposed_fg)

        folium.CircleMarker(location=[p['Lat'], p['Lon']], radius=0.1, opacity=0,
                            tooltip=folium.Tooltip(f"PROPOSED: {p['Name']}", permanent=True, direction='top')
                            ).add_to(proposed_labels_fg)

    # Add groups to map
    rail_fg.add_to(m)
    rail_labels_fg.add_to(m)
    hotspot_fg.add_to(m)
    proposed_fg.add_to(m)
    proposed_labels_fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Save map
    m.save(OUTPUT_MAP)
    print(f"Map saved to '{OUTPUT_MAP}'")

    # -------------------------
    # 7) Print top candidates
    # -------------------------
    print("\n--- TOP CANDIDATES FOR NEW STATIONS ---")
    if potential_df.empty:
        print("No candidates found matching criteria. Consider lowering thresholds or providing station_mappings with coordinates.")
    else:
        display_cols = ['Name', 'Bus_Boardings', 'Distance_Miles', 'Nearest_Rail', 'Routes']
        print(potential_df[display_cols].head(20).to_string(index=False))

    print("\n=== END: Analysis complete ===")


if __name__ == '__main__':
    run_analysis()
