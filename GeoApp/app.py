import streamlit as st
import geopandas as gpd
from shapely.geometry import box
import streamlit_js_eval as sje

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data
from api.openweathermap import get_weather_data
from utils.data_processing import load_polygons_from_geojson_within_extents
from utils.map_creation import create_map_with_features, display_theme_locations  # Import from map_creation
from prompts.language_prompts import prompts, themes


# Title for the Streamlit app
st.title("Geolocation with iframe in Streamlit")

def main():

    st.title("Interactive Geospatial App")
    geolocationData = sje.get_geolocation()
    user_location = {
        "latitude": geolocationData["coords"]["latitude"],
        "longitude": geolocationData["coords"]["longitude"]
    }

    # Proceed only if user location is available
    if user_location:
        lat, lon = user_location["latitude"], user_location["longitude"]
        st.success(f"Location retrieved: Latitude {lat}, Longitude {lon}")

        # GeoJSON file path
        file_path = './data/NParksParksandNatureReserves.geojson'
        # Load the polygon data from the GeoJSON file   
        try:
            gdf = gpd.read_file(file_path)
        except Exception as e:
            st.error(f"Error loading GeoJSON file: {e}")
            return

        postal_code = "123456"  # Example postal code
        dengue_clusters = get_dengue_clusters_with_extents(f"{lat-0.035},{lon-0.035},{lat+0.035},{lon+0.035}")  # Replace with your extents
        theme_data = []  # Replace with your theme data
        polygon_data = load_polygons_from_geojson_within_extents(gdf, box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025))

        # Call the function to create the map with the user's location and features
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

        user_input = st.text_input("Postal Code:")

        if st.button(prompts[st.session_state['language']]['enter_button'], key="enter_btn"):
            if user_input:
                latlon = get_latlon_from_postal(user_input)
                if latlon:
                    lat, lon = latlon
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

                    # Collect theme data
                    theme_data = []
                    for theme in themes:
                        theme_data.extend(get_theme_data(theme, extents))

                    create_map_with_features(lat, lon, user_input, dengue_clusters, theme_data, polygon_data, user_location)
                    display_theme_locations(theme_data)
                else:
                    st.error(prompts[st.session_state['language']]['error_message'])

    # Ensure the Restart button has a unique key
    if st.button("Restart", key="restart_btn"):
        st.session_state.clear()
        st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    main()