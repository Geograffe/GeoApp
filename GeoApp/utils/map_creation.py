import folium
from streamlit_folium import folium_static

def append_theme_markers_to_map(map_object, theme_data):
    if theme_data:
        for theme in theme_data:
            if "LatLng" in theme and isinstance(theme["LatLng"], str):
                lat_lng_list = eval(theme["LatLng"])
                if isinstance(lat_lng_list, list) and len(lat_lng_list) > 0:
                    lat_lng = lat_lng_list[0]
                    folium.Marker(
                        location=[lat_lng[1], lat_lng[0]], 
                        popup=f"{theme['DESCRIPTION']}",
                        icon=folium.Icon(color="green", icon="info-sign")
                    ).add_to(map_object)

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
            st.write(f"[Link]({theme.get('HYPERLINK', '#')})")
            st.write("---")
    else:
        st.write("No theme locations found.")
