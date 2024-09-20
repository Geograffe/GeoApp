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
    
def get_route(start, end, route_type, mode=None, date=None, time=None, max_walk_distance=None):
    url = f"https://www.onemap.gov.sg/api/public/routingsvc/route?start={start}&end={end}&routeType={route_type}"
    
    if route_type == "pt":
        # Add parameters for public transport (pt)
        url += f"&mode={mode}&date={date}&time={time}"
        if max_walk_distance:
            url += f"&maxWalkDistance={max_walk_distance}"

    headers = {"Authorization": f"Bearer {access_token}"}  # Add your valid access token here
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to retrieve route. Status Code: {response.status_code}")
        return None