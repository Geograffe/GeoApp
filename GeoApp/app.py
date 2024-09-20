import streamlit as st
import geopandas as gpd
from shapely.geometry import box
import streamlit_js_eval as sje
from datetime import datetime

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data, get_route
from api.openweathermap import get_weather_data
from utils.data_processing import load_polygons_from_geojson_within_extents
from utils.map_creation import create_map_with_features, display_theme_locations  # Import from map_creation
from prompts.language_prompts import prompts, themes


# Title for the Streamlit app
st.title("Geolocation with iframe in Streamlit")

def main():
    st.title("Interactive Geospatial App")
    
    geolocationData = sje.get_geolocation()

    # Check if geolocation data is available
    if geolocationData and "coords" in geolocationData:
        user_location = {
            "latitude": geolocationData["coords"]["latitude"],
            "longitude": geolocationData["coords"]["longitude"]
        }
    else:
        st.error("Unable to retrieve geolocation data. Please enable location services in your browser.")
        return  # Stop the execution here if geolocation is not available

    # Proceed only if user location is available
    lat, lon = user_location["latitude"], user_location["longitude"]
    st.success(f"Location retrieved: Latitude {lat}, Longitude {lon}")

    # GeoJSON file path
    file_path = 'GeoApp/data/NParksParksandNatureReserves.geojson'
    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return

    postal_code = "123456"  # Example postal code
    dengue_clusters = get_dengue_clusters_with_extents(f"{lat-0.035},{lon-0.035},{lat+0.035},{lon+0.035}")  # Replace with your extents
    theme_data = []  # Replace with your theme data
    polygon_data = load_polygons_from_geojson_within_extents(gdf, box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025))

    create_map_with_features(lat, lon, postal_code, dengue_clusters, theme_data, polygon_data, user_location)

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
        st.success(f"Selected Language: {st.session_state['language']}")
        prompt_text = prompts[st.session_state['language']]['prompt']
        st.write(prompt_text)

        user_input = st.text_input("Postal Code:", value=st.session_state.get("user_input", ""))

        if st.button(prompts[st.session_state['language']]['enter_button'], key="enter_btn"):
            if user_input:
                latlon = get_latlon_from_postal(user_input)
                if latlon:
                    lat, lon = latlon
                    st.session_state["user_input"] = user_input  # Save postal code input to session state
                    st.session_state["lat"] = lat
                    st.session_state["lon"] = lon
                    st.success(f"Location Found: Latitude {lat}, Longitude {lon}")

                    weather_data = get_weather_data(lat, lon)
                    st.subheader("Current Weather Conditions")
                    if weather_data:
                        st.write(f"**Weather Station**: {weather_data['name']}")
                        st.write(f"**Weather**: {weather_data['weather'][0]['description'].capitalize()}")
                        st.write(f"**Temperature**: {weather_data['main']['temp']}°C")
                        st.write(f"**Feels Like**: {weather_data['main']['feels_like']}°C")
                        st.write(f"**Humidity**: {weather_data['main']['humidity']}%")
                        st.write(f"**Wind Speed**: {weather_data['wind']['speed']} m/s, Direction: {weather_data['wind']['deg']}°")

                    extents = f"{lat-0.035},{lon-0.035},{lat+0.035},{lon+0.035}"
                    dengue_clusters = get_dengue_clusters_with_extents(extents)

                    extent_polygon = box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025)
                    polygon_data = load_polygons_from_geojson_within_extents(gdf, extent_polygon)

                    theme_data = []
                    for theme in themes:
                        theme_data.extend(get_theme_data(theme, extents))

                    # Select Route Type
                    route_type = st.selectbox("Select a Route Type", ["walk", "drive", "cycle", "pt"], key="route_type")

                    # Public transport specific parameters
                    if route_type == "pt":
                        mode = st.selectbox("Select Public Transport Mode", ["TRANSIT", "BUS", "RAIL"], key="mode")
                        max_walk_distance = st.number_input("Max Walk Distance (meters)", min_value=500, max_value=5000, step=500, value=1000, key="max_walk_distance")

                        # Get the current date and time
                        current_datetime = datetime.now()
                        date_str = current_datetime.strftime("%m-%d-%Y")
                        time_str = current_datetime.strftime("%H:%M:%S")

                    else:
                        mode = None
                        max_walk_distance = None
                        date_str = None
                        time_str = None

                    # Display theme locations and allow user to select one
                    selected_lat_lng = display_theme_locations(theme_data)

                    if selected_lat_lng:
                        start = f"{lat},{lon}"
                        end = selected_lat_lng

                        # Generate the route
                        route_data = get_route(start, end, route_type, mode, date_str, time_str, max_walk_distance)

                        if route_data and "route_geometry" in route_data:
                            route_geometry = route_data["route_geometry"]
                            create_map_with_features(lat, lon, user_input, dengue_clusters, theme_data, polygon_data, user_location, route_geometry)
                        else:
                            st.error("Failed to generate route or route geometry missing.")
                    else:
                        st.error("No location selected.")
                else:
                    st.error(prompts[st.session_state['language']]['error_message'])

    # Restart button
    if st.button("Restart", key="restart_btn"):
        st.session_state.clear()
        st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    main()
