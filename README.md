# Home Assistant Location Tracker

This project fetches location tracking data from Home Assistant and visualizes it on an old-timey map. 

It's intended to generate maps from your holidays or road trips.

## Features

- Fetches location data from Home Assistant API
- Processes and organizes the data using pandas
- Creates an interactive, old-timey style map using Folium
- Adds location markers and paths to the map

## Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Access to a Home Assistant instance with location tracking enabled
- Access to the [Thunderforest API](https://www.thunderforest.com/docs/apikeys/) for it's [Pioneer](https://www.thunderforest.com/maps/pioneer/) map tiles

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/ha-map-generator.git
   cd ha-map-generator
   ```

2. Install dependencies using Poetry:
   ```
   poetry install
   ```

3. Configure the Home Assistant connection:
   Copy `.env.example` to `.env` and update the variables in `.env`

## Usage

Run the script using Poetry and follow the prompts:
`python location_tracker.py`
