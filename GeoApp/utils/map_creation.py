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
        for theme in theme_data:
            st.write(f"**Name**: {theme.get('NAME', 'N/A')}")
            st.write(f"**Type**: {theme.get('THEMENAME', 'N/A')}")
            st.write(f"**Description**: {theme.get('DESCRIPTION', 'N/A')}")
            st.write(f"**Address**: {theme.get('ADDRESSSTREETNAME', 'N/A')} {theme.get('ADDRESSBLOCKHOUSENUMBER', '')}, {theme.get('ADDRESSPOSTALCODE', 'N/A')}")
            # Extract LatLng and display latitude and longitude
            lat_lng_str = theme.get('LatLng', None)
            if lat_lng_str:
                try:
                    lat_lng_list = eval(lat_lng_str)  # Safely convert string to list
                    if isinstance(lat_lng_list, list) and len(lat_lng_list) > 0:
                        lat_lng = lat_lng_list[0]
                        st.write(f"**Latitude**: {lat_lng[0]}")
                        st.write(f"**Longitude**: {lat_lng[1]}")
                except Exception as e:
                    st.write(f"Error parsing LatLng: {e}")
            st.write(f"[Link]({theme.get('HYPERLINK', '#')})")
            st.write("---")
    else:
        st.write("No theme locations found.")
