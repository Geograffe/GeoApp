import streamlit as st
import geopandas as gpd
from shapely.geometry import box
import streamlit_js_eval as sje
from datetime import datetime
import re

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data, get_route
from api.openweathermap import get_weather_data
from utils.data_processing import load_polygons_from_geojson_within_extents, extract_name_from_description 
from utils.map_creation import create_map_with_features, display_theme_locations
from prompts.language_prompts import prompts, themes

# Title for the Streamlit app
st.title("Geolocation with iframe in Streamlit")

def main():
    st.title("Interactive Geospatial App")

    # Fetch geolocation data (current location)
    geolocationData = sje.get_geolocation()

    # Check if geolocation data is available
    if geolocationData and "coords" in geolocationData:
        user_location = {
            "latitude": geolocationData["coords"]["latitude"],
            "longitude": geolocationData["coords"]["longitude"]
        }
    else:
        st.error("Unable to retrieve geolocation data. Please enable location services in your browser.")
        return  # Stop execution if geolocation is not available

    lat, lon = user_location["latitude"], user_location["longitude"]
    st.success(f"Current location retrieved: Latitude {lat}, Longitude {lon}")

    # Load the polygon data (GeoJSON)
    file_path = 'GeoApp/data/NParksParksandNatureReserves.geojson'
    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return

    dengue_clusters = get_dengue_clusters_with_extents(f"{lat-0.035},{lon-0.035},{lat+0.035},{lon+0.035}")
    polygon_data = load_polygons_from_geojson_within_extents(gdf, box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025))

    # Extract park names from the description in GeoJSON
    gdf['park_names'] = gdf['Description'].apply(extract_name_from_description)

    # Display map with current location and dengue clusters
    create_map_with_features(lat, lon, "Current Location", dengue_clusters, [], polygon_data, user_location)

    # Language selection logic
    if 'language' not in st.session_state:
        st.write("Please select your language:")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("English", key="english_btn"):
                st.session_state['language'] = 'English'
        with col2:
            if st.button("Bahasa Melayu", key="malay_btn"):
                st.session_state['language'] = 'Malay'
        with col3:
            if st.button("தமிழ்", key="tamil_btn"):
                st.session_state['language'] = 'Tamil'
        with col4:
            if st.button("中文", key="chinese_btn"):
                st.session_state['language'] = 'Chinese'

    # Main flow after language selection
    if 'language' in st.session_state:
        # Use the selected language for prompts
        lang_prompts = prompts[st.session_state['language']]
        st.success(f"Selected Language: {st.session_state['language']}")

        # Input postal code to set as the return/home point, display only once
        user_input = st.text_input(lang_prompts['prompt'], value=st.session_state.get("user_input", ""))  # Ensure prompt comes from language file

        if st.button(lang_prompts['enter_button'], key="enter_btn"):
            if user_input:
                latlon = get_latlon_from_postal(user_input)
                if latlon:
                    home_lat, home_lon = latlon
                    st.session_state["user_input"] = user_input  # Save the postal code
                    st.session_state["home_lat"] = home_lat     # Save the postal code lat
                    st.session_state["home_lon"] = home_lon     # Save the postal code lon
                    st.success(f"Home location set: Latitude {home_lat}, Longitude {home_lon}")

                    # Fetch weather data for the current location
                    weather_data = get_weather_data(lat, lon)
                    st.subheader(lang_prompts["weather_prompt"])  # Use the language-specific weather prompt
                    if weather_data:
                        st.write(f"**{lang_prompts['weather_station']}**: {weather_data['name']}")
                        st.write(f"**{lang_prompts['weather']}**: {weather_data['weather'][0]['description'].capitalize()}")
                        st.write(f"**{lang_prompts['temperature']}**: {weather_data['main']['temp']}°C")
                        st.write(f"**{lang_prompts['feels_like']}**: {weather_data['main']['feels_like']}°C")
                        st.write(f"**{lang_prompts['humidity']}**: {weather_data['main']['humidity']}%")
                        st.write(f"**{lang_prompts['wind_speed']}**: {weather_data['wind']['speed']} m/s, {lang_prompts['wind_direction']}: {weather_data['wind']['deg']}°")

                    extents = f"{lat-0.035},{lon-0.035},{lat+0.035},{lon+0.035}"
                    dengue_clusters = get_dengue_clusters_with_extents(extents)

                    extent_polygon = box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025)
                    polygon_data = load_polygons_from_geojson_within_extents(gdf, extent_polygon)

                    theme_data = []
                    for theme in themes:
                        theme_data.extend(get_theme_data(theme, extents))

                    # Save theme data in session state
                    st.session_state['theme_data'] = theme_data

    # Dropdown for selecting between Parks and Theme locations
    if 'theme_data' in st.session_state and st.session_state['theme_data']:
        theme_data = st.session_state['theme_data']
        location_type = st.selectbox("Choose Location Type", ["Parks", "Theme Locations"])

        # Dropdown logic for parks
        if location_type == "Parks":
            park_options = [name for name in gdf['park_names'] if name]
            selected_park = st.selectbox("Select a Park", park_options, key="selected_park")
            if selected_park:
                selected_park_data = gdf[gdf['park_names'] == selected_park].iloc[0]
                park_lat, park_lon = selected_park_data.geometry.centroid.y, selected_park_data.geometry.centroid.x
                st.session_state['selected_coords'] = (park_lat, park_lon)
                st.write(f"Selected Park Coordinates: Latitude {park_lat}, Longitude {park_lon}")

        # Dropdown logic for theme locations
        elif location_type == "Theme Locations":
            theme_data = st.session_state['theme_data']
            filtered_theme_data = [theme for theme in theme_data if theme.get('NAME', 'N/A') != 'N/A' and theme.get('NAME', '').strip()]
            if filtered_theme_data:
                theme_options = [f"{theme.get('NAME', 'Unknown')} - {theme.get('LatLng', 'N/A')}" for theme in filtered_theme_data]
                selected_theme = st.selectbox("Select a Theme Location", theme_options, key="selected_theme")
                if selected_theme:
                    lat_lng_str = selected_theme.split('-')[-1].strip()
                    selected_lat_lng = [float(coord) for coord in lat_lng_str.split(',')]
                    st.session_state['selected_coords'] = selected_lat_lng
                    st.write(f"Selected Theme Coordinates: {selected_lat_lng}")

    # Route calculation after selecting the location
    if 'selected_coords' in st.session_state:
        selected_lat_lng = st.session_state['selected_coords']
        start = f"{lat},{lon}"  # Use current geolocation as the start point
        end = f"{selected_lat_lng[0]},{selected_lat_lng[1]}"

        # Select route type
        route_type = st.selectbox("Select a Route Type", ["walk", "drive", "cycle", "pt"], key="route_type")
        if route_type == "pt":
            mode = st.selectbox("Select Public Transport Mode", ["TRANSIT", "BUS", "RAIL"], key="mode")
            max_walk_distance = st.number_input("Max Walk Distance (meters)", min_value=500, max_value=5000, step=500, value=1000, key="max_walk_distance")

            current_datetime = datetime.now()
            date_str = current_datetime.strftime("%m-%d-%Y")
            time_str = current_datetime.strftime("%H:%M:%S")

            route_data = get_route(start, end, route_type, mode, date_str, time_str, max_walk_distance)
        else:
            route_data = get_route(start, end, route_type)

        if route_data and "route_geometry" in route_data:
            route_geometry = route_data["route_geometry"]
            create_map_with_features(lat, lon, st.session_state.get('user_input', "Current Location"), dengue_clusters, [], polygon_data, user_location, route_geometry)

            if route_data and "route_summary" in route_data:
                total_time_seconds = route_data["route_summary"]["total_time"]
                total_distance_meters = route_data["route_summary"]["total_distance"]
                total_minutes = total_time_seconds // 60
                hours = total_minutes // 60
                minutes = total_minutes % 60
                time_str = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
                total_distance_km = total_distance_meters / 1000
                st.write(f"**Total Time**: {time_str}")
                st.write(f"**Total Distance**: {total_distance_km:.2f} km")
        else:
            st.error("Failed to generate route or route geometry missing.")

    # Return Home and Restart buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if "home_lat" in st.session_state and "home_lon" in st.session_state:
            if st.button("Return Home", key="return_home_btn"):
                start = f"{lat},{lon}"  # Current location
                end = f"{st.session_state['home_lat']},{st.session_state['home_lon']}"  # Home location
                route_type = "drive"
                route_data = get_route(start, end, route_type)
                if route_data and "route_geometry" in route_data:
                    route_geometry = route_data["route_geometry"]
                    create_map_with_features(lat, lon, "Current Location", dengue_clusters, theme_data, polygon_data, user_location, route_geometry)
                    if route_data and "route_summary" in route_data:
                        total_time_seconds = route_data["route_summary"]["total_time"]
                        total_distance_meters = route_data["route_summary"]["total_distance"]
                        total_minutes = total_time_seconds // 60
                        hours = total_minutes // 60
                        minutes = total_minutes % 60
                        time_str = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
                        total_distance_km = total_distance_meters / 1000
                        st.write(f"**Return Home Time**: {time_str}")
                        st.write(f"**Return Home Distance**: {total_distance_km:.2f} km")
                else:
                    st.error("Failed to generate return home route.")

    with col2:
        if st.button("Restart", key="restart_btn"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
