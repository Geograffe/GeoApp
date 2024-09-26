import streamlit as st 
import geopandas as gpd
from shapely.geometry import box
import streamlit_js_eval as sje
import pytz  
from datetime import datetime
import re

from api.onemap import get_latlon_from_postal, get_dengue_clusters_with_extents, get_theme_data, get_general_route, get_public_transport_route
from api.openweathermap import get_weather_data, get_forecast_data  # Import the new function
from utils.data_processing import load_polygons_from_geojson_within_extents, extract_name_from_description 
from utils.map_creation import create_map_with_features, display_theme_locations
from prompts.language_prompts import prompts, themes  # Updated to include translations

# Title for the Streamlit app
st.title("Jalan Jalan")

def main():
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
    
    # Define extent (bounding box)
    extent_polygon = box(lon - 0.025, lat - 0.025, lon + 0.025, lat + 0.025)
    
    # Filter parks within extent
    gdf_within_extent = gdf[gdf.geometry.within(extent_polygon)]
    
    # Extract park names within extent
    gdf_within_extent['park_names'] = gdf_within_extent['Description'].apply(extract_name_from_description)

    # Display map with current location and dengue clusters
    polygon_data = load_polygons_from_geojson_within_extents(gdf, extent_polygon)
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

    # Ensure language is selected before proceeding
    if 'language' in st.session_state:
        lang_prompts = prompts[st.session_state['language']]  # Now lang_prompts is safely initialized
        st.success(f"Selected Language: {st.session_state['language']}")
        
        # Continue with the rest of the app flow using `lang_prompts`
        user_input = st.text_input(lang_prompts['prompt'], value=st.session_state.get("user_input", ""))

        if st.button(lang_prompts['enter_button'], key="enter_btn"):
            if user_input:
                latlon = get_latlon_from_postal(user_input)
                if latlon:
                    home_lat, home_lon = latlon
                    st.session_state["user_input"] = user_input  # Save the postal code
                    st.session_state["home_lat"] = home_lat     # Save the postal code lat
                    st.session_state["home_lon"] = home_lon     # Save the postal code lon
                    st.success(f"{lang_prompts['weather_station']}: Latitude {home_lat}, Longitude {home_lon}")

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
                    else:
                        st.write(lang_prompts['error_message'])
                    
                    # Fetch forecast data for the next 1-2 hours
                    forecast_data = get_forecast_data(lat, lon)
                    st.subheader(lang_prompts["weather_prompt"])
                    
                    if forecast_data and 'list' in forecast_data:
                        sg_timezone = pytz.timezone("Asia/Singapore")

                        for entry in forecast_data['list'][:1]:  # Fetch next 1-2 hours
                            dt_txt = entry['dt_txt']
                            utc_time = datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
                            utc_time = utc_time.replace(tzinfo=pytz.utc)
                            sg_time = utc_time.astimezone(sg_timezone)
                            
                            temp = entry['main']['temp']
                            weather_description = entry['weather'][0]['description']
                            rain_chance = entry.get('pop', 0) * 100

                            st.write(f"**{sg_time.strftime('%Y-%m-%d %H:%M:%S')} SGT:**")
                            st.write(f"- {lang_prompts['temperature']}: {temp}°C")
                            st.write(f"- {lang_prompts['weather']}: {weather_description.capitalize()}")
                            st.write(f"- {lang_prompts['weather']} Chance: {rain_chance}%")

                            if rain_chance > 50:
                                st.warning(f"{lang_prompts['weather']}: Likely rain. Bring an umbrella or find shelter.")
                            if temp >= 32:
                                st.warning("⚠️ High temperature (≥32°C). Risk of heat stroke.")
                            elif temp >= 27:
                                st.warning("⚠️ Caution: High temperature (≥27°C). Risk of heat exhaustion.")
                    else:
                        st.write(lang_prompts['error_message'])

                    # Example Events
                    st.subheader("Example Events Retrieved from OnePA")
                    example_events = [
                        "XYZ CC - Pottery - Free",
                        "ABC CC - Guitar - $10",
                        "DEF CC - Yoga - $5",
                        "GHI CC - Dance - Free"
                    ]
                    
                    for event in example_events:
                        st.markdown(f"**{event}**")

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
        location_type = st.selectbox("Choose Location Type", ["Parks", "Community Centers and Historical Sites"])

        if location_type == "Parks":
            park_options = [name for name in gdf_within_extent['park_names'] if name]
            selected_park = st.selectbox("Select a Park", park_options, key="selected_park")
            if selected_park:
                selected_park_data = gdf_within_extent[gdf_within_extent['park_names'] == selected_park].iloc[0]
                park_lat, park_lon = selected_park_data.geometry.centroid.y, selected_park_data.geometry.centroid.x
                st.session_state['selected_coords'] = (park_lat, park_lon)
                st.write(f"Selected Park Coordinates: Latitude {park_lat}, Longitude {park_lon}")

        elif location_type == "Community Centers and Historical Sites":
            filtered_theme_data = [theme for theme in theme_data if theme.get('NAME', 'N/A') != 'N/A' and theme.get('NAME', '').strip()]
            if filtered_theme_data:
                theme_options = [f"{theme.get('NAME', 'Unknown')} - {theme.get('LatLng', 'N/A')}" for theme in filtered_theme_data]
                selected_theme = st.selectbox("Select a Theme Location", theme_options, key="selected_theme")
                if selected_theme:
                    lat_lng_str = selected_theme.split('-')[-1].strip()
                    selected_lat_lng = [float(coord) for coord in lat_lng_str.split(',')]
                    st.session_state['selected_coords'] = selected_lat_lng
                    st.write(f"Selected Theme Coordinates: {selected_lat_lng}")

    if 'selected_coords' in st.session_state:
        selected_lat_lng = st.session_state['selected_coords']
        start = f"{lat},{lon}"
        end = f"{selected_lat_lng[0]},{selected_lat_lng[1]}"

        route_type = st.selectbox(lang_prompts["choose_route"], ["walk", "drive", "cycle", "public transport"], key="route_type")
        
        if route_type == "public transport":
            mode = st.selectbox(lang_prompts["public_transport"], ["TRANSIT", "BUS", "RAIL"], key="mode")
            max_walk_distance = st.number_input(lang_prompts["max_walk"], min_value=500, max_value=5000, step=500, value=1000, key="max_walk_distance")
            
            current_datetime = datetime.now()
            date_str = current_datetime.strftime("%m-%d-%Y")
            time_str = current_datetime.strftime("%H:%M:%S")
            
            public_transport_route = get_public_transport_route(start, end, date_str, time_str, mode, max_walk_distance)

            if public_transport_route:
                st.write(f"**{lang_prompts['fare']}**: {public_transport_route['fare']}")
                st.write(f"**{lang_prompts['total_duration']}**: {public_transport_route['total_duration']} minutes")
                st.subheader(lang_prompts["transit_details"])
                for transit in public_transport_route['transit_details']:
                    st.write(f"**{lang_prompts['mode']}**: {transit['mode']}, **{lang_prompts['route']}**: {transit['route']}, **{lang_prompts['agency']}**: {transit['agency']}")
                
                route_geometry = public_transport_route['route_geometry']
                if route_geometry:
                    create_map_with_features(lat, lon, st.session_state.get('user_input', "Current Location"), dengue_clusters, [], polygon_data, user_location, route_geometry)
            else:
                st.error(lang_prompts['error_message'])
        
        else:
            general_route_data = get_general_route(start, end, route_type)

            if general_route_data and "route_geometry" in general_route_data:
                route_geometry = general_route_data["route_geometry"]
                create_map_with_features(lat, lon, st.session_state.get('user_input', "Current Location"), dengue_clusters, [], polygon_data, user_location, route_geometry)

                if general_route_data and "route_summary" in general_route_data:
                    total_time_seconds = general_route_data["route_summary"]["total_time"]
                    total_distance_meters = general_route_data["route_summary"]["total_distance"]
                    total_minutes = total_time_seconds // 60
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    time_str = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
                    total_distance_km = total_distance_meters / 1000
                    st.write(f"**{lang_prompts['total_time']}**: {time_str}")
                    st.write(f"**{lang_prompts['total_distance']}**: {total_distance_km:.2f} km")
            else:
                st.error(lang_prompts['error_message'])

    # Return Home and Restart buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if "home_lat" in st.session_state and "home_lon" in st.session_state:
            route_type = st.selectbox(lang_prompts["choose_route"], ["walk", "drive", "cycle", "public transport"], key="home_route_type")

            if route_type == "public transport":
                mode = st.selectbox(lang_prompts["public_transport"], ["TRANSIT", "BUS", "RAIL"], key="home_mode")
                max_walk_distance = st.number_input(lang_prompts["max_walk"], min_value=500, max_value=5000, step=500, value=1000, key="home_max_walk")

            if st.button(lang_prompts["return_home"], key="return_home_btn"):
                start = f"{lat},{lon}"
                end = f"{st.session_state['home_lat']},{st.session_state['home_lon']}"

                if route_type == "public transport":
                    date_str = datetime.now().strftime("%m-%d-%Y")
                    time_str = datetime.now().strftime("%H:%M:%S")

                    route_data = get_public_transport_route(start, end, date_str, time_str, mode, max_walk_distance)

                    if route_data and "route_geometry" in route_data:
                        route_geometry = route_data["route_geometry"]
                        create_map_with_features(lat, lon, "Current Location", dengue_clusters, theme_data, polygon_data, user_location, route_geometry)

                        if "total_duration" in route_data:
                            total_minutes = route_data["total_duration"]
                            hours = total_minutes // 60
                            minutes = total_minutes % 60
                            time_str = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
                            st.write(f"**{lang_prompts['return_home_time']}**: {time_str}")

                        st.write(f"**{lang_prompts['fare']}**: {route_data.get('fare', 'N/A')}")

                        st.subheader(lang_prompts["transit_steps"])
                        for transit in route_data['transit_details']:
                            st.write(f"- **{lang_prompts['mode']}**: {transit['mode']}, **{lang_prompts['route']}**: {transit['route']}, **{lang_prompts['agency']}**: {transit['agency']}")

                    else:
                        st.error(lang_prompts['error_message'])

                else:
                    general_route_data = get_general_route(start, end, route_type)

                    if general_route_data and "route_geometry" in general_route_data:
                        route_geometry = general_route_data["route_geometry"]
                        create_map_with_features(lat, lon, "Current Location", dengue_clusters, theme_data, polygon_data, user_location, route_geometry)

                        if general_route_data and "route_summary" in general_route_data:
                            total_time_seconds = general_route_data["route_summary"]["total_time"]
                            total_distance_meters = general_route_data["route_summary"]["total_distance"]
                            total_minutes = total_time_seconds // 60
                            hours = total_minutes // 60
                            minutes = total_minutes % 60
                            time_str = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
                            total_distance_km = total_distance_meters / 1000
                            st.write(f"**{lang_prompts['total_time']}**: {time_str}")
                            st.write(f"**{lang_prompts['total_distance']}**: {total_distance_km:.2f} km")
                    else:
                        st.error(lang_prompts['error_message'])

    with col2:
        if st.button(lang_prompts["restart"], key="restart_btn"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
