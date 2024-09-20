import streamlit as st
import geopandas as gpd
from shapely.geometry import box, Point
import streamlit_js_eval as sje
from datetime import datetime

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data, get_route
from api.openweathermap import get_weather_data
from utils.data_processing import load_polygons_from_geojson_within_extents
from utils.map_creation import create_map_with_features
from prompts.language_prompts import prompts, themes

# Title for the Streamlit app
st.title("Jalan Jalan App")

def main():
    # Initialize session state values if not already set
    if 'user_input' not in st.session_state:
        st.session_state['user_input'] = ""

    if 'home_lat' not in st.session_state:
        st.session_state['home_lat'] = None

    if 'home_lon' not in st.session_state:
        st.session_state['home_lon'] = None

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

    # Get dengue clusters and polygon data
    dengue_clusters = get_dengue_clusters_with_extents(f"{lat-0.035},{lon-0.035},{lat+0.035},{lon+0.035}")
    extent_polygon = box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025)

    # Load nearby polygons and find nearest points to user location
    polygon_data = load_polygons_from_geojson_within_extents(gdf, extent_polygon, user_location)

    # Extract the names of the polygons and their nearest points
    polygon_options = []
    nearest_points = []

    # Loop through polygon data and extract relevant details
    for polygon in polygon_data:
        if 'coordinates' in polygon and isinstance(polygon['coordinates'], list):
            coords = polygon['coordinates']
            try:
                if isinstance(coords[0], list):
                    point_coords = coords[0][0]
                else:
                    point_coords = coords

                if len(point_coords) >= 2:
                    lon, lat = point_coords[:2]
                    polygon_options.append(polygon['description'])
                    nearest_points.append(Point(lon, lat))
                else:
                    st.warning(f"Skipping invalid point with insufficient dimensions: {point_coords}")

            except Exception as e:
                st.error(f"Error processing coordinates: {coords}. Error: {e}")
                continue

    # Display map with current location
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
        lang_prompts = prompts[st.session_state['language']]
        st.success(f"Selected Language: {st.session_state['language']}")

        # Input postal code to set as the return/home point, display only once
        user_input = st.text_input(lang_prompts['prompt'], value=st.session_state.get("user_input", ""))

        if st.button(lang_prompts['enter_button'], key="enter_btn"):
            if user_input:
                latlon = get_latlon_from_postal(user_input)
                if latlon:
                    home_lat, home_lon = latlon
                    st.session_state["user_input"] = user_input
                    st.session_state["home_lat"] = home_lat
                    st.session_state["home_lon"] = home_lon
                    st.success(f"Home location set: Latitude {home_lat}, Longitude {home_lon}")

                    # Fetch weather data for the current location
                    weather_data = get_weather_data(lat, lon)
                    st.subheader(lang_prompts["weather_prompt"])
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
                    polygon_data = load_polygons_from_geojson_within_extents(gdf, extent_polygon, user_location)

                    theme_data = []
                    for theme in themes:
                        theme_data.extend(get_theme_data(theme, extents))

                    # Save theme data in session state
                    st.session_state['theme_data'] = theme_data

    # Handle theme selection and routing
    if 'theme_data' in st.session_state:
        theme_data = st.session_state['theme_data']

        # Filter out themes with 'N/A' names
        filtered_theme_data = [theme for theme in theme_data if theme.get('NAME', 'N/A') != 'N/A' and theme.get('NAME', '').strip()]

        if filtered_theme_data:
            theme_options = [f"{theme.get('NAME', 'Unknown')} - {theme.get('LatLng', 'N/A')}" for theme in filtered_theme_data]

            selected_theme = st.selectbox("Select a Theme Location", theme_options, key="selected_theme")

            if selected_theme:
                lat_lng_str = selected_theme.split('-')[-1].strip()
                try:
                    selected_lat_lng = [float(coord) for coord in lat_lng_str.split(',')]
                    st.session_state['selected_lat_lng'] = selected_lat_lng
                    st.write(f"Selected Location Coordinates: {selected_lat_lng}")
                except ValueError:
                    st.error("Failed to parse the selected location's coordinates.")
        else:
            st.write("No valid theme locations available for selection.")

    # Select park and generate route
    if polygon_options:
        selected_park = st.selectbox("Select a Nearby Park", polygon_options)
        if selected_park:
            selected_park_index = polygon_options.index(selected_park)
            nearest_park_point = nearest_points[selected_park_index]

            start = f"{lat},{lon}"
            end = f"{nearest_park_point.y},{nearest_park_point.x}"

            route_type = st.selectbox("Select a Route Type (for Park)", ["walk", "drive", "cycle", "pt"], key="park_route_type")
            route_data = get_route(start, end, route_type)

            if route_data and "route_geometry" in route_data:
                route_geometry = route_data["route_geometry"]
                create_map_with_features(lat, lon, st.session_state['user_input'], dengue_clusters, theme_data, polygon_data, user_location, route_geometry)

                if "route_summary" in route_data:
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
                start = f"{lat},{lon}"
                end = f"{st.session_state['home_lat']},{st.session_state['home_lon']}"

                route_type = "drive"
                route_data = get_route(start, end, route_type)

                if route_data and "route_geometry" in route_data:
                    route_geometry = route_data["route_geometry"]
                    create_map_with_features(lat, lon, st.session_state['user_input'], dengue_clusters, theme_data, polygon_data, user_location, route_geometry)

                    if "route_summary" in route_data:
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
                    st.error("Failed to generate return home route.")

    with col2:
        if st.button("Restart", key="restart_btn"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
