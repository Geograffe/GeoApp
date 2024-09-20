# Geospatial-Innovation-Hackathon
Here’s a standard `README.md` file template for your geospatial app project. You can adjust the content based on your specific needs:

---

# Geospatial App with OneMap and OpenWeatherMap

## Overview

This project is a Streamlit-based geospatial app that leverages **OneMap API** and **OpenWeatherMap API** to provide users with current geolocation data, weather information, and route generation functionality. Users can select their return address by entering a postal code and choose from various public points of interest (POIs) such as parks, community clubs, and libraries. The app also provides real-time routing based on current location using different modes of transportation such as walking, driving, cycling, and public transport.

## Features

- **Geolocation Services**: Fetches the user’s current location using their browser's geolocation capabilities.
- **Weather Information**: Provides real-time weather information for the user’s current location using OpenWeatherMap API.
- **Dengue Cluster Data**: Fetches and displays dengue clusters within a certain extent using OneMap’s dengue data.
- **POI Theme Selection**: Allows users to select points of interest (POIs) such as parks, community clubs, and other public locations using OneMap's theme data.
- **Route Calculation**: Users can generate routes from their current location to selected POIs or return home. The app supports walking, cycling, driving, and public transport.
- **Return Home Button**: A persistent button for routing back to the saved home (postal code) location.
- **Multi-language Support**: The app supports English, Malay, Tamil, and Chinese, with localized prompts and weather data presentation.

## Tech Stack

- **Backend**: Python, Streamlit
- **APIs**: 
  - OneMap API (for geocoding, reverse geocoding, and routing)
  - OpenWeatherMap API (for weather data)
- **Geospatial Libraries**: 
  - Geopandas (for handling GeoJSON files)
  - Shapely (for geometric operations)
  
## Setup and Installation

### Prerequisites

- Python 3.x
- A valid **OneMap API** access token.
- A valid **OpenWeatherMap API** key.

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/geospatial-app.git
    cd geospatial-app
    ```

2. **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # For Windows use: venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up your environment variables:**

   Create a `.env` file in the project root directory and add your API keys:

    ```env
    ONEMAP_API_TOKEN=your_onemap_token_here
    OPENWEATHER_API_KEY=your_openweather_key_here
    ```

5. **Run the Streamlit app:**

    ```bash
    streamlit run app.py
    ```

## Usage

1. **Select Language**: Upon starting the app, choose your preferred language (English, Malay, Tamil, or Chinese).
2. **Enter Postal Code**: Enter the postal code of your return address (home location).
3. **View Current Location**: The app will retrieve and display your current location and the corresponding weather data.
4. **Select a Theme/POI**: Choose a public location to navigate to from the list of available POIs.
5. **Generate Route**: Select your desired mode of transportation (walking, driving, cycling, public transport) and the app will calculate the route from your current location to the selected POI.
6. **Return Home**: Use the **Return Home** button to generate a route back to your saved home address.

## API Integration

### OneMap API

- **Geocoding and Reverse Geocoding**: Converts postal codes to latitude/longitude and vice versa.
- **Theme Data**: Retrieves and displays public points of interest (POIs) based on selected themes.
- **Routing**: Generates routes using multiple modes of transportation (walk, drive, cycle, public transport).

### OpenWeatherMap API

- **Weather Data**: Provides real-time weather information for the user's current location, including temperature, humidity, wind speed, and more.

## Project Structure

```bash
geospatial-app/
│
├── GeoApp/
│   ├── api/
│   │   ├── onemap.py          # OneMap API integration
│   │   ├── openweathermap.py  # OpenWeatherMap API integration
│   ├── data/
│   │   ├── NParksParksandNatureReserves.geojson  # GeoJSON file for parks and nature reserves
│   ├── utils/
│   │   ├── data_processing.py  # Utility functions for data handling
│   │   ├── map_creation.py     # Map creation and feature display functions
│   ├── prompts/
│   │   ├── language_prompts.py # Multi-language prompts
│   └── app.py                 # Main application script
│
├── .env                        # Environment file (API keys)
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Future Improvements

- **User Authentication**: Allow users to log in and save their favorite routes and locations.
- **Enhanced POI Filtering**: Provide more robust filtering of points of interest based on user preferences.
- **Historical Weather Data**: Option to view historical weather data for specific locations.
- **Map Styling**: Implement custom map styles and themes for better visual representation.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more information.

## Contact

For any questions or issues, please contact [Jeng Siang] at [jengsiang.seem@gmail.com].

