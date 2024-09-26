# openweathermap.py

import requests

API_KEY = 'your_api_key'  # Replace with your OpenWeatherMap API key

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
