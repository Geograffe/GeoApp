import requests
import streamlit as st
from datetime import datetime
import polyline

# Your access token
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0Mjc3MTk1Y2Q2NzdkZmI4ZDA2NWM4MGMzOGU0ZjhhMyIsImlzcyI6Imh0dHA6Ly9pbnRlcm5hbC1hbGItb20tcHJkZXppdC1pdC0xMjIzNjk4OTkyLmFwLXNvdXRoZWFzdC0xLmVsYi5hbWF6b25hd3MuY29tL2FwaS92Mi91c2VyL3Bhc3N3b3JkIiwiaWF0IjoxNzI2NzQ4MDA0LCJleHAiOjE3MjcwMDcyMDQsIm5iZiI6MTcyNjc0ODAwNCwianRpIjoiZ2puQTFBNmlacEEzVWJEUCIsInVzZXJfaWQiOjQ2MTIsImZvcmV2ZXIiOmZhbHNlfQ.E8-g2SUQhYVpNtaCu4otBOqBJwG-xMxOCYRaU7LUzJM"  # Replace this with your actual OneMap token


def get_latlon_from_postal(postal_code):
    url = "https://www.onemap.gov.sg/api/common/elastic/search"
    params = {
        "searchVal": postal_code,
        "returnGeom": "Y",
        "getAddrDetails": "Y",
        "pageNum": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and len(data['results']) > 0:
            lat = float(data['results'][0]['LATITUDE'])
            lon = float(data['results'][0]['LONGITUDE'])
            return lat, lon
    st.error("No results found for the postal code.")
    return None

def get_dengue_clusters_with_extents(extents):
    url = f"https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme?queryName=dengue_cluster&extents={extents}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("SrchResults", [])
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return None

def get_theme_data(query_name, extents):
    url = f"https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme?queryName={query_name}&extents={extents}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("SrchResults", [])
    else:
        st.error(f"Failed to retrieve data for {query_name}. Status Code: {response.status_code}")
        return []
    

# Function to handle walking, driving, cycling routes
def get_general_route(start, end, route_type):
    url = f"https://www.onemap.gov.sg/api/public/routingsvc/route?start={start}&end={end}&routeType={route_type}"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to retrieve {route_type} route. Status Code: {response.status_code}")
        return None

def get_public_transport_route(start, end, date, time, mode, max_walk_distance=1000, num_itineraries=1):
    url = f"https://www.onemap.gov.sg/api/public/routingsvc/route?start={start}&end={end}&routeType=pt&date={date}&time={time}&mode={mode}&maxWalkDistance={max_walk_distance}&numItineraries={num_itineraries}"

    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"Failed to retrieve public transport route. Status Code: {response.status_code}")
        return None

    data = response.json()
    
    if "plan" not in data or "itineraries" not in data["plan"]:
        st.error("No valid public transport routes found.")
        return None
    
    itinerary = data["plan"]["itineraries"][0]  # First itinerary
    fare = itinerary.get("fare", "N/A")  # Get fare if available

    # Process legs of the trip to extract bus and train details and route geometry
    transit_details = []
    decoded_route_geometry = []  # List to hold combined decoded coordinates
    for leg in itinerary["legs"]:
        if leg["transitLeg"]:  # Check if it's a transit leg (bus/train)
            mode = leg["mode"]
            route = leg.get("route", "")
            agency = leg.get("agencyName", "")
            transit_details.append({
                "mode": mode,
                "route": route,
                "agency": agency
            })

        # Decode each leg's geometry and append to the overall route
        if "legGeometry" in leg and "points" in leg["legGeometry"]:
            leg_points = leg["legGeometry"]["points"]
            decoded_leg = polyline.decode(leg_points)  # Decode the leg geometry
            decoded_route_geometry.extend(decoded_leg)  # Add decoded points to the route

    return {
        "fare": fare,
        "transit_details": transit_details,
        "route_geometry": decoded_route_geometry,  # List of decoded coordinates
        "total_duration": itinerary["duration"] // 60  # Convert seconds to minutes
    }
