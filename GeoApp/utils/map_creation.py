import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

def append_theme_markers_to_map(map_object, theme_data):
    # Initialize marker cluster for better management of many markers
    marker_cluster = MarkerCluster().add_to(map_object)

    if theme_data:
        for theme in theme_data:
            if "LatLng" in theme and isinstance(theme["LatLng"], str):
                try:
                    lat_lng_list = eval(theme["LatLng"])
                    if isinstance(lat_lng_list, list) and len(lat_lng_list) > 0:
                        lat_lng = lat_lng_list[0]
                        
                        # Ensure lat_lng contains valid coordinates
                        if len(lat_lng) == 2 and all(isinstance(coord, (int, float)) for coord in lat_lng):
                            folium.Marker(
                                location=[lat_lng[1], lat_lng[0]], 
                                popup=folium.Popup(f"<b>Description:</b> {theme['DESCRIPTION']}", max_width=300),
                                icon=folium.Icon(color="red", icon="info-sign"),  # More vibrant color
                                tooltip=f"Click for more info"
                            ).add_to(marker_cluster)
                        else:
                            print(f"Invalid lat_lng format for theme: {theme}")
                except (SyntaxError, ValueError):
                    print(f"Error evaluating LatLng for theme: {theme}")

def create_map_with_features(lat, lon, postal_code, dengue_clusters, theme_data, polygon_data, user_location=None):
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], popup=f"Postal Code: {postal_code}").add_to(m)
    
    if user_location:
        folium.Marker([user_location['latitude'], user_location['longitude']],
                      popup="Your Location", icon=folium.Icon(color="blue")).add_to(m)

    if dengue_clusters:
        for cluster in dengue_clusters:
            if "LatLng" in cluster and isinstance(cluster["LatLng"], str):
                lat_lng_list = eval(cluster["LatLng"])
                folium.Polygon(
                    locations=[(coord[1], coord[0]) for coord in lat_lng_list],
                    color="red",
                    fill=True,
                    fill_opacity=0.5,
                    popup=f"Dengue Cluster: {cluster['DESCRIPTION']}, Cases: {cluster['CASE_SIZE']}"
                ).add_to(m)

    for polygon in polygon_data:
        if isinstance(polygon['coordinates'][0], list):
            for sub_polygon in polygon['coordinates']:
                folium.Polygon(
                    locations=[(coord[1], coord[0]) for coord in sub_polygon],
                    color='green', fill=True, fill_opacity=0.5,
                    popup=polygon['description']
                ).add_to(m)
        else:
            folium.Polygon(
                locations=[(coord[1], coord[0]) for coord in polygon['coordinates']],
                color='green', fill=True, fill_opacity=0.5,
                popup=polygon['description']
            ).add_to(m)

    append_theme_markers_to_map(m, theme_data)
    folium_static(m)

def display_theme_locations(theme_data):
    import streamlit as st
    
    st.subheader("Nearby Theme Locations")

    if theme_data:
        # Create a list of names for the radio button
        locations = [
            {
                "name": theme.get('NAME', 'N/A'),
                "description": theme.get('DESCRIPTION', 'N/A'),
                "type": theme.get('THEMENAME', 'N/A'),
                "address": f"{theme.get('ADDRESSSTREETNAME', 'N/A')} {theme.get('ADDRESSBLOCKHOUSENUMBER', '')}, {theme.get('ADDRESSPOSTALCODE', 'N/A')}",
                "lat_lng_str": theme.get('LatLng', None),
                "link": theme.get('HYPERLINK', '#')
            }
            for theme in theme_data if theme.get('NAME', 'N/A') != "N/A" and theme.get('NAME').strip()
        ]

        if not locations:
            st.write("No valid theme locations found.")
            return

        # Create a radio button for selecting a location
        selected_location = st.radio("Select a Location:", [loc["name"] for loc in locations])

        # Once selected, print the location details
        st.write(f"**Selected Location**: {selected_location}")

        # Optionally, display details of the selected location
        for loc in locations:
            if loc["name"] == selected_location:
                st.write(f"**Name**: {loc['name']}")
                st.write(f"**Type**: {loc['type']}")
                st.write(f"**Description**: {loc['description']}")
                st.write(f"**Address**: {loc['address']}")
                
                # Extract LatLng and display latitude and longitude
                lat_lng_str = loc["lat_lng_str"]
                if lat_lng_str:
                    try:
                        lat_lng_list = lat_lng_str.split(",")  # Split the string by commas
                        if len(lat_lng_list) == 2:  # Ensure it has two values (lat, lng)
                            lat = float(lat_lng_list[0].strip())  # Convert to float and strip any whitespace
                            lng = float(lat_lng_list[1].strip())  # Convert to float and strip any whitespace
                            st.write(f"**Latitude**: {lat}")
                            st.write(f"**Longitude**: {lng}")
                        else:
                            st.write("LatLng data is incomplete.")
                    except ValueError as e:
                        st.write(f"Error parsing LatLng: {e}")
                
                st.write(f"[Link]({loc['link']})")
                st.write("---")
                break
    else:
        st.write("No theme locations found.")
