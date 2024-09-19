import streamlit as st
import streamlit.components.v1 as components
from pyngrok import ngrok

# Function to create a secure ngrok tunnel (optional)
def create_ngrok_tunnel():
    # Start ngrok tunnel to the streamlit app
    public_url = ngrok.connect(8501)
    st.write(f"App is accessible at {public_url}")

# Call ngrok tunnel on load (optional)
if 'ngrok_tunnel_created' not in st.session_state:
    create_ngrok_tunnel()
    st.session_state['ngrok_tunnel_created'] = True

# JavaScript code to continuously get geolocation from the browser and post it to Streamlit
geo_location_js = """
    <script>
        // Function to send location to Streamlit continuously
        function trackLocation() {
            navigator.geolocation.watchPosition(
                (position) => {
                    // Get latitude and longitude
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    // Post the latitude and longitude to Streamlit via postMessage
                    window.parent.postMessage({lat: lat, lon: lon}, "*");
                },
                (error) => {
                    document.body.innerHTML = `<p>Unable to retrieve your location. Please allow location access.</p>`;
                },
                { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }  // Track with high accuracy
            );
        }

        // Call the function to start tracking location
        trackLocation();
    </script>
"""

# Embed the JavaScript to start location tracking
components.html(geo_location_js, height=0)

# Function to process the coordinates
def display_coordinates():
    lat = st.session_state.get("lat")
    lon = st.session_state.get("lon")
    
    if lat and lon:
        st.write(f"Your current location is: Latitude {lat}, Longitude {lon}")
    else:
        st.write("Waiting for location data...")

# Listen for messages from the JavaScript (coordinates)
if 'lat' not in st.session_state:
    st.session_state['lat'] = None
    st.session_state['lon'] = None

# Continuously update the coordinates if we get them from the browser
message = st.experimental_get_query_params()
if "lat" in message and "lon" in message:
    st.session_state['lat'] = message['lat'][0]
    st.session_state['lon'] = message['lon'][0]

# Display coordinates
display_coordinates()

# Automatically refresh the page to show updated location
st.rerun()  # Automatically rerun the app to keep location updated
