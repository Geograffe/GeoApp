import requests
import streamlit as st
from datetime import datetime

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
    
def get_route(start, end, route_type, mode=None, date_str=None, time_str=None, max_walk_distance=None):
    # Base URL for OneMap routing service
    url = "https://www.onemap.gov.sg/api/public/routingsvc/route"
    
    # Prepare parameters for the request
    params = {
        "start": start,
        "end": end,
        "routeType": route_type
    }
    
    # Additional parameters for public transport (pt)
    if route_type == "pt":
        if mode and date_str and time_str:
            params.update({
                "mode": mode,  # Public transport mode: TRANSIT, BUS, RAIL
                "date": date_str,
                "time": time_str,
                "maxWalkDistance": max_walk_distance or 1000,  # Default to 1000 meters if not provided
            })
        else:
            st.error("Missing required parameters for public transport route.")
            return None

    headers = {"Authorization": "Bearer YOUR_API_TOKEN"}

    # Make the API request
    response = requests.get(url, params=params, headers=headers)
    
    # Handle the response
    if response.status_code == 200:
        data = response.json()
        if "route_geometry" in data:
            return data  # Return the full data including route_geometry
        else:
            st.error("No route geometry found in the response.")
            st.write(data)  # Log the full response for debugging
            return None
    else:
        st.error(f"Failed to retrieve route. Status code: {response.status_code}")
        st.write(response.text)  # Log the full response for debugging
        return None