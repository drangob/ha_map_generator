import os
from typing import List
from datetime import datetime, timedelta
import requests
import pandas as pd
import folium
from folium.plugins import AntPath
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
THUNDERFOREST_API_KEY = os.getenv('THUNDERFOREST_API_KEY')
THUNDERFOREST_MAP_TYPE = os.getenv('THUNDERFOREST_MAP_TYPE', 'pioneer')

HA_HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

def get_location_data(entity_ids: List[str], days: int) -> pd.DataFrame:
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    end_date = datetime.now().isoformat()
    responses = [
        requests.get(
            f"{HA_URL}/api/history/period/{start_date}",
            headers=HA_HEADERS,
            params={"filter_entity_id": entity_id, "end_time": end_date}
        )
        for entity_id in entity_ids
    ]
    all_location_data = []
    for response in responses:
        if response.status_code == 200:
            data = response.json()
        else:
            error_message = response.json().get('message', 'No error message provided')
            raise Exception(f"Failed to fetch data: HTTP {response.status_code}. Error: {error_message}")
        for state in data[0]:
            attrs = state.get("attributes", {})
            if "latitude" in attrs and "longitude" in attrs:
                all_location_data.append({
                    "timestamp": state["last_updated"],
                    "latitude": attrs["latitude"],
                    "longitude": attrs["longitude"]
                })
    location_df = pd.DataFrame(all_location_data)
    location_df.sort_values(by="timestamp", inplace=True)
    return location_df

def create_old_timey_map(df: pd.DataFrame) -> folium.Map:
    m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=10)
    folium.TileLayer(
        tiles=f'https://{{s}}.tile.thunderforest.com/{THUNDERFOREST_MAP_TYPE}/{{z}}/{{x}}/{{y}}.png?apikey={THUNDERFOREST_API_KEY}',
        attr='&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    ).add_to(m)
    locations = df[["latitude", "longitude"]].values.tolist()
    AntPath(
        locations,
        color="#8B4513",
        weight=4,
        opacity=1,
        hardwareAccelerated=True,
        pulse_color='#8B4513',
        delay=0,
        dash_array=[0, 100],
        use_segments=True
    ).add_to(m)
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=1,
            popup=row["timestamp"],
            color="#8B4513",
            fill=True,
            fillColor="#8B4513",
            fillOpacity=1,
            stroke=False
        ).add_to(m)
    return m

def get_device_tracker_entity_ids() -> List[str]:
    resp = requests.get(f"{HA_URL}/api/states", headers=HA_HEADERS)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch person entities: HTTP {resp.status_code}")
    persons = [e for e in resp.json() if e['entity_id'].startswith('person.')]
    print("Available entities:")
    for i, entity in enumerate(persons, 1):
        print(f"{i}. {entity['entity_id']}")
    selection = input("Enter the numbers of the entities you want to track (comma-separated): ")
    selected_indices = [int(index.strip()) - 1 for index in selection.split(',')]
    selected_persons = [persons[index] for index in selected_indices]
    return [p['attributes']['source'] for p in selected_persons]

def main():
    entity_ids = get_device_tracker_entity_ids()
    days = int(input("Enter the number of days of history to fetch: "))
    df = get_location_data(entity_ids, days)
    old_timey_map = create_old_timey_map(df)
    
    # Prompt for filename
    default_filename = "map.html"
    filename = input(f"Enter filename to save the map [{default_filename}]: ").strip() or default_filename
    
    # Check if file exists
    if os.path.exists(filename):
        confirm = input(f"File '{filename}' exists. Overwrite? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted. Map not saved.")
            return
    old_timey_map.save(filename)
    print(f"Map saved as '{filename}'")

if __name__ == "__main__":
    main()