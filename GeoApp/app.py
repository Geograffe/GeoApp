import streamlit as st
import geopandas as gpd
from shapely.geometry import box
import streamlit_js_eval as sje
from datetime import datetime

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data, get_route
from api.openweathermap import get_weather_data
from utils.data_processing import load_polygons_from_geojson_within_extents
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
    file_path = '/GeoApp/data/NParksParksandNatureReserves.geojson'
    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return

    extents_polygon = box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025)
    polygon_data = load_polygons_from_geojson_within_extents(gdf, extents_polygon)

    # Display map with current location
    create_map_with_features(lat, lon, "Current Location", [], [], polygon_data, user_location)

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

    # Park selection and routing
    if polygon_data:
        park_options = [f"{park['name']}" for park in polygon_data]

        selected_park = st.selectbox("Select a Park", park_options, key="selected_park")

        if selected_park:
            selected_park_data = next((park for park in polygon_data if park['name'] == selected_park), None)
            if selected_park_data:
                park_lat, park_lon = selected_park_data['centroid']
                st.session_state['selected_park_coords'] = (park_lat, park_lon)
                st.write(f"Selected Park Coordinates: Latitude {park_lat}, Longitude {park_lon}")

    # Route calculation after selecting the park
    if 'selected_park_coords' in st.session_state:
        park_lat, park_lon = st.session_state['selected_park_coords']
        start = f"{lat},{lon}"  # Use current geolocation as the start point
        end = f"{park_lat},{park_lon}"

        # Select route type
        route_type = st.selectbox("Select a Route Type", ["walk", "drive", "cycle"], key="route_type")

        route_data = get_route(start, end, route_type)

        if route_data and "route_geometry" in route_data:
            route_geometry = route_data["route_geometry"]
            create_map_with_features(lat, lon, "Current Location", [], [], polygon_data, user_location, route_geometry)
            
            if route_data and "route_summary" in route_data:
                total_time_seconds = route_data["route_summary"]["total_time"]  # Total time in seconds
                total_distance_meters = route_data["route_summary"]["total_distance"]  # Total distance in meters

                # Convert time to minutes and hours
                total_minutes = total_time_seconds // 60
                hours = total_minutes // 60
                minutes = total_minutes % 60

                if hours > 0:
                    time_str = f"{hours} hours {minutes} minutes"
                else:
                    time_str = f"{minutes} minutes"

                # Convert distance to kilometers
                total_distance_km = total_distance_meters / 1000

                # Display the total time and distance
                st.write(f"**Total Time**: {time_str}")
                st.write(f"**Total Distance**: {total_distance_km:.2f} km")
        else:
            st.error("Failed to generate route or route geometry missing.")

    # Return Home and Restart buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if "home_lat" in st.session_state and "home_lon" in st.session_state:
            home_lat = st.session_state['home_lat']
            home_lon = st.session_state['home_lon']
            if st.button("Return Home"):
                # Calculate route back to home
                home_route_data = get_route(f"{lat},{lon}", f"{home_lat},{home_lon}", route_type)

                if home_route_data and "route_geometry" in home_route_data:
                    home_route_geometry = home_route_data["route_geometry"]
                    create_map_with_features(lat, lon, "Current Location", [], [], polygon_data, user_location, home_route_geometry)

                    if home_route_data and "route_summary" in home_route_data:
                        home_total_time_seconds = home_route_data["route_summary"]["total_time"]
                        home_total_distance_meters = home_route_data["route_summary"]["total_distance"]

                        home_total_minutes = home_total_time_seconds // 60
                        home_hours = home_total_minutes // 60
                        home_minutes = home_total_minutes % 60

                        if home_hours > 0:
                            home_time_str = f"{home_hours} hours {home_minutes} minutes"
                        else:
                            home_time_str = f"{home_minutes} minutes"

                        home_total_distance_km = home_total_distance_meters / 1000

                        st.write(f"**Return Home Time**: {home_time_str}")
                        st.write(f"**Return Home Distance**: {home_total_distance_km:.2f} km")
                else:
                    st.error("Failed to generate return home route or route geometry missing.")

    with col2:
        if st.button("Restart App"):
            # Clear session state
            for key in st.session_state.keys():
                del st.session_state[key]
            st.experimental_rerun()

if __name__ == '__main__':
    main()
