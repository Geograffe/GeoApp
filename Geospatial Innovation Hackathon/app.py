import streamlit as st
import geopandas as gpd
from shapely.geometry import box
from streamlit_folium import folium_static
import folium
import streamlit.components.v1 as components

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data
from api.openweathermap import get_weather_data
from utils.data_processing import load_polygons_from_geojson_within_extents
from utils.map_creation import create_map_with_features, display_theme_locations  # Import from map_creation
from prompts.language_prompts import prompts, themes

# JavaScript code to listen for messages from the iframe and reload Streamlit with the updated coordinates
geo_js = """
<script>
  window.addEventListener("message", (event) => {
    if (event.data && event.data.latitude && event.data.longitude) {
      const queryParams = new URLSearchParams(window.location.search);
      queryParams.set("latitude", event.data.latitude);
      queryParams.set("longitude", event.data.longitude);
      window.location.search = queryParams.toString(); // This reloads the page with updated params
    }
  });
</script>
"""

def main():
    st.title("Interactive Geospatial App")

    # Load the polygon data from the GeoJSON file
    file_path = 'file_path = 'data\NParksParksandNatureReserves.geojson'
    
    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return

    # Inject the Geolocation HTML and JavaScript from the separate HTML file
    with open('geolocation.html', 'r') as f:
        geolocation_html = f.read()

    # Inject the HTML and JavaScript for continuous location updates
    components.html(geolocation_html, height=400)  # Adjust height based on content

    # Inject the JavaScript listener for updating coordinates from the iframe
    components.html(geo_js, height=0)

    # Check if geolocation data (latitude and longitude) is available from query parameters
    query_params = st.query_params  # Use the new query_params method
    user_location = None
    if "latitude" in query_params and "longitude" in query_params:
        user_location = {
            "latitude": float(query_params["latitude"]),
            "longitude": float(query_params["longitude"])
        }
        st.success(f"Current Location: Latitude {user_location['latitude']}, Longitude {user_location['longitude']}")
    else:
        st.error("Unable to retrieve your current location. Please ensure location services are enabled.")

    # Proceed only if user location is available
    if user_location:
        lat, lon = user_location['latitude'], user_location['longitude']

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