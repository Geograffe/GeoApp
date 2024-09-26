# openweathermap.py

import requests

API_KEY = '9e6085041c62f51b85975d38a06264c6'  # Replace with your OpenWeatherMap API key

def get_weather_data(lat, lon):
    # Existing function to get current weather data
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_forecast_data(lat, lon):
    # New function to get 5-day/3-hour forecast data
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
