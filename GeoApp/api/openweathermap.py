import requests
import streamlit as st

# OpenWeatherMap API key
OWM_API_KEY = "9e6085041c62f51b85975d38a06264c6"  # Replace with your OpenWeatherMap API key

def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to retrieve weather data. Status Code: {response.status_code}")
        return None
