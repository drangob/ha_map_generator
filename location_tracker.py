import requests
import pandas as pd
import folium
from folium.plugins import AntPath

# Home Assistant API configuration
from dotenv import load_dotenv
import os

load_dotenv()

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
THUNDERFOREST_API_KEY = os.getenv('THUNDERFOREST_API_KEY')

HA_HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

def get_location_data(entity_ids: list[str], days: int):    
    # Calculate the start date
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    # Make the API request from the start date until now
    end_date = datetime.now().isoformat()
    response = requests.get(
        f"{HA_URL}/api/history/period/{start_date}",
        headers=HA_HEADERS,
        params={
            "filter_entity_id": entity_ids,
            "end_time": end_date
        }
    )
    
    if response.status_code == 200:
        data = response.json()
    else:
        error_message = response.json().get('message', 'No error message provided')
        raise Exception(f"Failed to fetch data: HTTP {response.status_code}. Error: {error_message}")
    
    # Extract location data from the response
    location_data = []
    for state in data[0]:
        if "latitude" in state["attributes"] and "longitude" in state["attributes"]:
            location_data.append({
                "timestamp": state["last_updated"],
                "latitude": state["attributes"]["latitude"],
                "longitude": state["attributes"]["longitude"]
            })
    return pd.DataFrame(location_data)

def create_old_timey_map(df):
    # Create a base map
    m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=10)
    
    # Add an old-timey tileset
    folium.TileLayer(
        tiles=f'https://{{s}}.tile.thunderforest.com/pioneer/{{z}}/{{x}}/{{y}}.png?apikey={THUNDERFOREST_API_KEY}',
        attr='&copy; <a href="http://www.thunderforest.com/">Thunderforest</a>, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    ).add_to(m)
    
    # Add path between points (without animation)
    # Create a smooth, hand-drawn looking path
    locations = df[["latitude", "longitude"]].values.tolist()
    AntPath(
        locations, 
        color="#8B4513", 
        weight=4,  # Increased thickness
        opacity=1,
        hardwareAccelerated=True,
        pulse_color='#8B4513',  # Same as the line color
        delay=0,  # No delay for animation
        dash_array=[0, 100],  # Continuous line
        use_segments=True
    ).add_to(m)

    # Add small markers at each point (optional, you can remove if not needed)
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

def get_device_tracker_entity_ids():
    # Get the list of persons
    entities_response = requests.get(f"{HA_URL}/api/states", headers=HA_HEADERS)
    if entities_response.status_code == 200:
        persons = [entity for entity in entities_response.json() if entity['entity_id'].startswith(('person.'))]
    else:
        raise Exception(f"Failed to fetch person entities: HTTP {entities_response.status_code}")

    # Prompt the user to select a person
    print("Available entities:")
    for i, entity in enumerate(persons, 1):
        print(f"{i}. {entity['entity_id']}")
    
    selection = int(input("Enter the number of the entity you want to track: ")) - 1
    selected_person = persons[selection]

    # using the source for now rather than the device_trackers list
    device_tracker_entity_ids = [selected_person['attributes']['source']]

    return device_tracker_entity_ids


def main():
    entity_ids = get_device_tracker_entity_ids()
    days = int(input("Enter the number of days of history to fetch: "))
    df = get_location_data(entity_ids, days)
    old_timey_map = create_old_timey_map(df)
    old_timey_map.save("old_timey_location_map.html")
    print("Map saved as 'old_timey_location_map.html'")

if __name__ == "__main__":
    main()