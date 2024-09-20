import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import polyline

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

def create_map_with_features(lat, lon, postal_code, dengue_clusters, theme_data, polygon_data, user_location=None, route_geometry=None):
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], popup=f"Postal Code: {postal_code}").add_to(m)
    
    if user_location:
        folium.Marker([user_location['latitude'], user_location['longitude']],
                      popup="Your Location", icon=folium.Icon(color="blue")).add_to(m)

    # Decode and display the route on the map
    if route_geometry:
        decoded_route = polyline.decode(route_geometry)
        folium.PolyLine(locations=[(lat, lon) for lat, lon in decoded_route], color="blue", weight=5).add_to(m)

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
        # Ensure the coordinates are correctly nested
        if isinstance(polygon['coordinates'][0], list):  # For MultiPolygon
            for sub_polygon in polygon['coordinates']:
                folium.Polygon(
                    locations=[(coord[1], coord[0]) for coord in sub_polygon],
                    color='green', fill=True, fill_opacity=0.5,
                    popup=polygon['description']
                ).add_to(m)
        else:  # For Polygon
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
        # Create a list of available locations
        locations = [
            {
                "name": theme.get('NAME', 'N/A'),
                "lat_lng": theme.get('LatLng', None),
                "address": f"{theme.get('ADDRESSSTREETNAME', 'N/A')} {theme.get('ADDRESSBLOCKHOUSENUMBER', '')}, {theme.get('ADDRESSPOSTALCODE', 'N/A')}"
            }
            for theme in theme_data if theme.get('NAME', 'N/A') != "N/A" and theme.get('LatLng', None) is not None
        ]

        # Radio button for selecting a location to route to
        selected_location = st.radio("Select a Location to Route To:", [loc["name"] for loc in locations])

        # Display the selected location details
        for loc in locations:
            if loc["name"] == selected_location:
                st.write(f"**Selected Location**: {loc['name']}")
                st.write(f"**Address**: {loc['address']}")
                return loc["lat_lng"]  # Return the selected lat_lng string
    else:
        st.write("No theme locations found.")
        return None



