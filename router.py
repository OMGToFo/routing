#2024.05.07 update wikipedia scrape
#2024.09.05 addrd chatopenai, booking.com and bigger navigation button

import streamlit as st
import requests
import pandas as pd

import folium

from streamlit_folium import st_folium

import time

from datetime import datetime
from datetime import date
from datetime import timedelta

from streamlit_js_eval import streamlit_js_eval, copy_to_clipboard, create_share_link, get_geolocation
import json

#password secrets handling
import os
from dotenv import load_dotenv
load_dotenv(".env")


rapidApiKey = os.getenv("rapidApiKey")
yelp_api_key = os.getenv("yelp_api_key")
ocm_api_key = os.getenv("ocm_api_key")
api_key =  os.getenv("googleMaps_api_key")
X_RapidAPI_Key = os.getenv("X-RapidAPI-Key")


from geopy.geocoders import Nominatim

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

#wikipedia info
import requests
from bs4 import BeautifulSoup

POI_df = pd.DataFrame()
OverviewSumDistance = 0
OverviewSumTime = 0
visaTripadvisorHotel = False

import openai #old code
from openai import OpenAI

# Set up OpenAI API
openai_api_key = ""  # Replace with your actual API key






# Function to scrape Wikipedia information for a given location name
def scrape_wikipedia(location_name):
    wikipedia_url = f"https://en.wikipedia.org/wiki/{location_name.replace(' ', '_')}"
    response = requests.get(wikipedia_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.find("div", {"id": "mw-content-text"})
        paragraphs = content.find_all("p")
        wiki_info = "\n".join([p.get_text() for p in paragraphs if p.get_text()])
        return wiki_info
    else:
        return None




def get_lat_long_from_address(address):
   locator = Nominatim(user_agent='thomasTest')
   location = locator.geocode(address)

   return str(location.latitude) +"," + str(location.longitude)





def get_nearby_restaurants(latitude, longitude): #by yelp

   yelp_api_url = 'https://api.yelp.com/v3/businesses/search'

   headers = {'Authorization': f'Bearer {yelp_api_key}'}
   params = {'latitude': latitude, 'longitude': longitude, 'categories': 'restaurants', 'limit': 10}

   response = requests.get(yelp_api_url, headers=headers, params=params)
   data = response.json()

   return data['businesses']



def get_nearby_charging_stations(latitude, longitude):
   # Use Open Charge Map API to get nearby EV charging stations

   ocm_api_url = 'https://api.openchargemap.io/v3/poi/'

   params = {
      'output': 'json',
      'latitude': last_lat,
      'longitude': last_lon,
      'distance': 30,  # Search radius in kilometers
      'distanceunit': 'KM',
      #'countrycode': 'CH',  # Replace with the appropriate country code
      'maxresults': 10  # Maximum number of results
   }

   headers = {'X-API-Key': ocm_api_key}

   response = requests.get(ocm_api_url, params=params, headers=headers)
   data = response.json()

   return data


#NOT USED HERE - Function to fetch location info from Wikipedia ################################
def get_location_info(latitude, longitude):
   base_url = "https://en.wikipedia.org/w/api.php"
   params = {
      'format': 'json',
      'action': 'query',
      'list': 'geosearch',
      'gscoord': f'{latitude}|{longitude}',
      'gsradius': '5000',  # You can adjust the radius as needed
   }
   response = requests.get(base_url, params=params)
   data = response.json()

   if 'query' in data and 'geosearch' in data['query']:
      # Extract relevant information from the response
      location_info = data['query']['geosearch'][0]
      title = location_info['title']
      pageid = location_info['pageid']

      # Fetch detailed information using the title or pageid
      detailed_info = get_detailed_info(title)
      # You can use the title or pageid to fetch more information if needed
      #st.write(f' {title}')
      #st.write(f'Page ID: {pageid}')
      st.write(detailed_info)

   else:
      st.warning('Location information not found on Wikipedia.')


def get_detailed_info(title):
   base_url = "https://en.wikipedia.org/w/api.php"
   params = {
      'format': 'json',
      'action': 'query',
      'prop': 'extracts',
      'titles': title,
      'exintro': True,
   }
   response = requests.get(base_url, params=params)
   data = response.json()

   if 'query' in data and 'pages' in data['query']:
      # Extract detailed information from the response
      page = next(iter(data['query']['pages'].values()))
      detailed_info = page['extract']


      # Clean up HTML tags using BeautifulSoup
      soup = BeautifulSoup(detailed_info, 'html.parser')
      cleaned_text = soup.get_text(separator='\n\n')  # Separate paragraphs with two newlines
      #st.write(cleaned_text)
      return cleaned_text
   else:
      return 'Detailed information not found.'

########End of Wikipedia fetching##############################################




# Define the list of google type words
typeList = [
    "restaurant","accounting", "airport", "amusement_park", "aquarium", "art_gallery",
    "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store",
    "book_store", "bowling_alley", "bus_station", "cafe", "campground",
    "car_dealer", "car_rental", "car_repair", "car_wash", "casino", "cemetery",
    "church", "city_hall", "clothing_store", "convenience_store", "courthouse",
    "dentist", "department_store", "doctor", "drugstore", "electrician",
    "electronics_store", "embassy", "fire_station", "florist", "funeral_home",
    "furniture_store", "gas_station", "gym", "hair_care", "hardware_store",
    "hindu_temple", "home_goods_store", "hospital", "insurance_agency",
    "jewelry_store", "laundry", "lawyer", "library", "light_rail_station",
    "liquor_store", "local_government_office", "locksmith", "lodging",
    "meal_delivery", "meal_takeaway", "mosque", "movie_rental", "movie_theater",
    "moving_company", "museum", "night_club", "painter", "park", "parking",
    "pet_store", "pharmacy", "physiotherapist", "plumber", "police", "post_office",
    "primary_school", "real_estate_agency", "POI", "roofing_contractor",
    "rv_park", "school", "secondary_school", "shoe_store", "shopping_mall", "spa",
    "stadium", "storage", "store", "subway_station", "supermarket", "synagogue",
    "taxi_stand", "tourist_attraction", "train_station", "transit_station",
    "travel_agency", "university", "veterinary_care", "zoo"
]



st.title("Simple Route Planner")


#####get time #######################################

today = date.today()
todayString = str(today)

tomorrow = today + timedelta(1)


######  get location #################################

loc = get_geolocation()
if loc:
    # gelocExpander = st.expander("Show geolocation data of your location:")
    # with gelocExpander:
    # st.write(f"Your coordinates are {loc}")

    lat_actual = loc['coords']['latitude']
    long_actual = loc['coords']['longitude']

    actualLocation = (lat_actual, long_actual)
    # Initialize Nominatim API
    geolocator = Nominatim(user_agent="actualLocationAdress")

    # Get the location (address)
    ActuallocationAdress = geolocator.reverse(actualLocation, exactly_one=True)
    time.sleep(1)

    # Extract the address
    Actualaddress = ActuallocationAdress.address
    # Output the address
    # st.write(f"The address detected for yor location is: {Actualaddress}")

    # st.write("actualLocation:", actualLocation)

    # editable Dataframe with Stops

    st.info("Enter stops and means of transport" + " (default is set to drive)")
    df = pd.DataFrame(columns=['Location', 'Transport'])
    transport = ['drive', 'truck', 'bicycle', 'walk']
    config = {
        'name': st.column_config.TextColumn('Location', width='large', required=True),
        # 'age': st.column_config.NumberColumn('Age (years)', min_value=0, max_value=122),
        'Transport': st.column_config.SelectboxColumn('Transport', options=transport)
    }

    # Set the value of the first cell in the 'Location' column
    df.at[0, 'Location'] = Actualaddress

    # Reset index and drop the old index column
    df.reset_index(drop=True, inplace=True)

    result_df = st.data_editor(df, column_config=config, num_rows='dynamic',,width=400)

    st.divider()
    st.info("Show POIs at stops")
    togglecol1, togglecol2, togglecol3 = st.columns(3)
    visaWiki = togglecol1.toggle("Show Wikipedia Information", value=False, key="hej wiki")
    visaRestaurants = togglecol2.toggle("Show restaurants by Yelp")
    visaChargingStations = togglecol3.toggle("Show Charging Stations", value=False, key="hej igen")

    togglecol4, togglecol5, togglecol6 = st.columns(3)
    visaGooglePOI = togglecol4.toggle("Show POIs by Google", value=False, key="hey Google")
    if visaGooglePOI:
        st.divider()
        st.text("Settings for Google Search:")
        eingabeCol1, eingabeCol2 = st.columns([1, 4])

        radiusEingabe = eingabeCol1.number_input("Radius (km)", value=5)
        radiusEingabe = radiusEingabe * 1000

        # Create a select box for the user to choose from the list
        selected_type = eingabeCol2.selectbox("Choose a type", typeList)
        st.divider()

    #visaTripadvisorHotel = togglecol5.toggle("Show Hotels from Tripadvisor", value=False, key="hey Tripadvisor")

    visaBookingComHotel = togglecol5.toggle("Show Hotels from Booking.com", value=False, key="hey BookingCom")
    if visaBookingComHotel:
        st.divider()
        st.text("Settings for Hotel Bookings:")
        bookingCo1, bookingCol2,bookingCol3 = st.columns(3)
        numerOfAdults = bookingCo1.number_input("Number of adults", value=1)
        numerOfAdultsString = str(numerOfAdults)

        CheckInDate = bookingCol2.date_input("Check-In Date", today, key="end")
        CheckOutDate = bookingCol3.date_input("Check-Out Date", tomorrow, key="start")
        st.divider()


    visaTrafficByWaze = togglecol6.toggle("Show traffic messages from Waze", value=False, key="hey Waze")


    visaRoutingtipaByOpenAI = st.toggle("Show Tips from OpenAI")
    if visaRoutingtipaByOpenAI:
        openai_api_key = st.text_input("Enter OpemAI key")
        pre_Input = st.text_input("Prompt", value="Please give me a short summary of interesting stops on the following route: ")


    st.divider()

    #Make Checkbox larger
    css = """
    <style>
    [data-baseweb="checkbox"] [data-testid="stCheckbox"] p {
    /* Styles for the label text for checkbox */
    font-size: 4rem;
    width: 300px;
    margin-top: 4rem;
}
    [data-testid="stCheckbox"] label span {
        /* Styles the checkbox */
        height: 3rem;
        width: 3rem;
    }
    </style>
    """

    checkboxCol1, checkboxCol2,checkboxCol3 = st.columns([10,30,60],vertical_alignment="center")

    st.write(css, unsafe_allow_html=True) #make checkbox larger
    navigationStart = checkboxCol1.checkbox('   ')
    checkboxCol2.subheader("Navigate!")
    checkboxCol3.write("")

    if navigationStart:

        # Initialize geolocator
        geolocator = Nominatim(user_agent="geoapiThomasRouting")

        # Add rate limiter to avoid overwhelming the geocoding service
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


        # Create functions to fetch latitude and longitude
        def get_latitude(location):
            location = geolocator.geocode(location)
            return location.latitude if location else None


        def get_longitude(location):
            location = geolocator.geocode(location)
            return location.longitude if location else None


        # Replace empty or missing values in the 'Transport' column with 'drive'
        result_df['Transport'].fillna('drive', inplace=True)
        result_df['Transport'].replace('', 'drive', inplace=True)
        result_df['Transport'].replace('None', 'drive', inplace=True)

        # Apply functions to DataFrame
        result_df['Latitude'] = result_df['Location'].apply(get_latitude)
        result_df['Longitude'] = result_df['Location'].apply(get_longitude)

        #st.write(result_df)

        st.subheader("")
        st.divider()


        # API request function
        def get_route(lat1, lon1, lat2, lon2, mode):
            url = "https://route-and-directions.p.rapidapi.com/v1/routing"
            querystring = {"waypoints": f"{lat1},{lon1}|{lat2},{lon2}", "mode": mode}
            headers = {
                "X-RapidAPI-Key": "your_api_key",  # Replace with your RapidAPI key
                "X-RapidAPI-Host": "route-and-directions.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers, params=querystring)
            return response.json()

        # Create a Folium map centered at the midpoint of the locations
        RouteOverViewMap = folium.Map(location=[result_df['Latitude'].mean(), result_df['Longitude'].mean()], zoom_start=8)

        # Iterate through each consecutive pair of locations to fetch routes

        RouteLegMaps = folium.Map(location=[result_df['Latitude'].mean(), result_df['Longitude'].mean()], zoom_start=8)

        Route = 0

        for i in range(len(result_df) - 1):
            lat1, lon1 = str(result_df.iloc[i]['Latitude']), str(result_df.iloc[i]['Longitude'])
            lat2, lon2 = str(result_df.iloc[i + 1]['Latitude']), str(result_df.iloc[i + 1]['Longitude'])
            mode = result_df.iloc[i]['Transport']

            Route = i + 1
            LegStartLocation = str(result_df.iloc[i]['Location'])
            LegEndLocation = str(result_df.iloc[i + 1]['Location'])
            LegTransport = str(result_df.iloc[i]['Transport'])

            _="""
            st.write("lat1", lat1)
            st.write("lon1", lon1)
            st.write("lat2", lat2)
            st.write("lon2", lon2)
            st.write("mode", mode)
            """

            url = "https://route-and-directions.p.rapidapi.com/v1/routing"
            querystring = {"waypoints": f"{lat1},{lon1}|{lat2},{lon2}", "mode": str(mode)}
            headers = {
                "X-RapidAPI-Key": X_RapidAPI_Key,
                "X-RapidAPI-Host": "route-and-directions.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    time.sleep(1) #new 2024.08.24

                    if 'features' in response_data:
                        mls = response_data['features'][0]['geometry']['coordinates']
                        points = [(i[1], i[0]) for i in mls[0]]
                        folium.Marker(points[0]).add_to(RouteOverViewMap)
                        folium.Marker(points[-1]).add_to(RouteOverViewMap)
                        folium.PolyLine(points, weight=5, opacity=1).add_to(RouteOverViewMap)

                        st.subheader("Segment " + str(Route))
                        st.info(LegTransport + " from: " + "\n " + LegStartLocation + "\n " + "to: " + LegEndLocation)
                        mlsTabelle = response.json()['features'][0]['properties']['legs'][0]['steps']
                        df_mlsTabelle = pd.json_normalize(
                            mlsTabelle)  # .rename(columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]

                        # create optimal zoom
                        Zoom_df = pd.DataFrame(mls[0]).rename(columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]
                        #st.write(Zoom_df)
                        Leg_sw = Zoom_df[['Lat', 'Lon']].min().values.tolist()
                        Leg_ne = Zoom_df[['Lat', 'Lon']].max().values.tolist()

                        #Find last point
                        last_lat = Zoom_df['Lat'].iloc[-1]
                        last_lon = Zoom_df['Lon'].iloc[-1]


                        df_mlsTabelle['Leg'] = Route

                        legDistance = df_mlsTabelle['distance'].sum() / 1000
                        legTime = df_mlsTabelle['time'].sum() / 60
                        LegCol1, LegCol2 = st.columns(2)
                        LegCol1.metric(label="Distance (km)", value=legDistance.round(0))
                        LegCol2.metric(label="Duration (min)", value=legTime.round(0))

                        #LegMaps
                        Legpoints = [(i[1], i[0]) for i in mls[0]]
                        folium.Marker(Legpoints[0]).add_to(RouteLegMaps)
                        folium.Marker(Legpoints[-1]).add_to(RouteLegMaps)
                        folium.PolyLine(Legpoints, weight=5, opacity=1).add_to(RouteLegMaps)





                        if visaTrafficByWaze: ##########################

                            Leg_sw_raw = Zoom_df[['Lat', 'Lon']].min().values

                            # Extract the latitude and longitude
                            latitude_sw = Leg_sw_raw[0]
                            longitude_sw = Leg_sw_raw[1]

                            # Format the values to a string with the desired precision
                            Leg_sw_formatted_string = f"{latitude_sw:.5f}, {longitude_sw:.5f}"

                            Leg_ne_raw = Zoom_df[['Lat', 'Lon']].max().values

                            # Extract the latitude and longitude
                            latitude_ne = Leg_ne_raw[0]
                            longitude_ne = Leg_ne_raw[1]

                            # Format the values to a string with the desired precision
                            Leg_ne_formatted_string = f"{latitude_ne:.5f}, {longitude_ne:.5f}"


                            # Define the URL and query parameters for the API request
                            url = "https://waze-api.p.rapidapi.com/alerts"
                            #querystring = {"bottom-left": "46.26954, 27.22208", "top-right": "47.03122, 27.99128",
                            #               "limit": "20"}
                            querystring = {"bottom-left": Leg_sw_formatted_string, "top-right": Leg_ne_formatted_string,
                                           "limit": "20"}


                            # Define the headers for the API request
                            headers = {
                                "x-rapidapi-key": X_RapidAPI_Key,
                                "x-rapidapi-host": "waze-api.p.rapidapi.com"
                            }

                            # Make the API request and get the response
                            response = requests.get(url, headers=headers, params=querystring)

                            time.sleep(1)

                            # Check if the response status code is 200 (OK)
                            if response.status_code == 200:
                                try:
                                    data = response.json()

                                    # Convert timestamps to human-readable format
                                    for alert in data:
                                        alert['timestamp'] = datetime.utcfromtimestamp(
                                            alert['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')

                                    # Create a DataFrame from the response data
                                    traffic_df = pd.DataFrame(data)



                                    # Create a Folium map centered around the average location of the alerts
                                    #map_center = [df['locationY'].mean(), df['locationX'].mean()]
                                    #m = folium.Map(location=map_center, zoom_start=12)

                                    # Add markers for each alert to the map
                                    for index, row in traffic_df.iterrows():
                                        folium.Marker(
                                            location=[row['locationY'], row['locationX']],
                                            popup=f"Type: {row['type']}<br>Street: {row['street']}",
                                            icon=folium.Icon(color="red" if row['type'] == "POLICE" else "blue")
                                        ).add_to(RouteLegMaps)

                                except ValueError:
                                    st.error("Error parsing JSON response")
                            else:
                                st.error(f"API request from Waze failed with status code {response.status_code}")




                        #### DESTINATIONMAPS ###########################################################
                        # Prepare a map centered around the destination
                        destinationMap = folium.Map(location=[last_lat, last_lon], zoom_start=13)
                        folium.Marker(
                            [last_lat, last_lon], popup="Destination", tooltip="Destination"
                        ).add_to(destinationMap)


                        if visaRestaurants:  # by yelp
                            # Display nearby restaurants
                            restaurants = get_nearby_restaurants(last_lat, last_lon)
                            # Create a Pandas DataFrame to store restaurant information
                            restaurant_df = pd.DataFrame({
                                'Name': [restaurant['name'] for restaurant in restaurants],
                                'Phone': [restaurant['phone'] for restaurant in restaurants],
                                'Rating': [restaurant['rating'] for restaurant in restaurants],
                                'Location': [f"{restaurant['location']['address1']}, {restaurant['location']['city']}" for
                                             restaurant in restaurants],

                                'Distance': [restaurant['distance'] for restaurant in restaurants],

                                'Category': [f"{restaurant['categories'][0]['title']}" for
                                             restaurant in restaurants],

                                'Reviews on Yelp': [restaurant['review_count'] for restaurant in restaurants],

                                'Latitude': [f"{restaurant['coordinates']['latitude']}" for
                                             restaurant in restaurants],
                                'Longitude': [f"{restaurant['coordinates']['longitude']}" for
                                              restaurant in restaurants],

                            })
                            restaurant_df.sort_values(by=['Distance'], inplace=True)

                            # Add markers for each yelp restaurant
                            for i, row in restaurant_df.iterrows():
                                folium.Marker(
                                    location=[row['Latitude'], row['Longitude']],
                                    popup=f"{row['Name']} - Rating: {row['Rating']}",
                                    icon=folium.Icon(color='red'),
                                    tooltip=f"{row['Name']} - {row['Category']} - Rating: {row['Rating']}",
                                ).add_to(destinationMap)




                        if visaChargingStations:

                            # Get nearby EV charging stations
                            charging_stations = get_nearby_charging_stations(last_lat, last_lon)

                            # alle infos vom api st.write(charging_stations)

                            # Create a Pandas DataFrame to store charging station information
                            charging_station_df = pd.DataFrame({
                                'Name': [station['AddressInfo']['Title'] for station in charging_stations],
                                'Location': [
                                    f"{station['AddressInfo']['AddressLine1']}, {station['AddressInfo']['Town']}" for
                                    station in charging_stations],
                                'Latitude': [station['AddressInfo']['Latitude'] for station in charging_stations],
                                'Longitude': [station['AddressInfo']['Longitude'] for station in charging_stations],
                                'Distance': [station['AddressInfo']['Distance'] for station in charging_stations],
                                'KW': [station['Connections'][0]['PowerKW'] for station in charging_stations],
                                # 'Operational': [station['Connections'][0]['StatusType'] for station in charging_stations],
                                'AccessComments': [station['AddressInfo']['AccessComments'] for station in
                                                   charging_stations],
                                # 'AccessComments': [station['AddressInfo']['AccessComments'] for station in charging_stations],
                                # 'ID_Test': [station['Connections'][0]['StatusType']['ID'] for station in charging_stations],
                            })

                            charging_station_df.sort_values(by=['Distance'], inplace=True)

                            # charging_map = folium.Map(location=map_center, zoom_start=12)

                            # Add markers for charging stations
                            for i, row in charging_station_df.iterrows():
                                folium.Marker(
                                    location=[row['Latitude'], row['Longitude']],
                                    popup=f"{row['Name']}\n{row['Location']}\n - KW: {row['KW']}",
                                    tooltip=f"{row['Name']}\n{row['Location']}\n  - KW:  {row['KW']}",
                                    icon=folium.Icon(color='green', icon='plug')  # Green marker for charging stations
                                ).add_to(destinationMap)




                        if visaGooglePOI: ########################################

                            # selected_type = "restaurant"

                            # Function to fetch nearby POIs using Google Places API
                            def get_nearby_POI(api_key, latitude, longitude, radius=radiusEingabe, types=selected_type):
                                base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                                params = {
                                    'location': f'{latitude},{longitude}',
                                    'radius': radius,
                                    'types': types,
                                    'key': api_key,
                                }
                                response = requests.get(base_url, params=params)
                                data = response.json()
                                return data.get('results', [])


                            # Google Map Api
                            # Create a list to store DataFrames for each POI
                            POI_dfs = []

                            # Create a DataFrame to store POI information
                            columns = ['Name', 'Type', 'Price Level', 'Rating', 'Opening Hours']
                            POI_df = pd.DataFrame(columns=columns)

                            POIs = get_nearby_POI(api_key, last_lat, last_lon)
                            sorted_POIs = sorted(POIs, key=lambda x: x.get('name', 'N/A'))

                            # Display the results and populate the DataFrame
                            if POIs:

                                for idx, POI in enumerate(sorted_POIs):
                                    name = POI.get('name', 'N/A')
                                    r_type = ', '.join(POI.get('types', []))
                                    price_level = POI.get('price_level', 'N/A')
                                    rating = POI.get('rating', 'N/A')
                                    lat = POI['geometry']['location']['lat']
                                    lng = POI['geometry']['location']['lng']

                                    # Add marker for each POI
                                    folium.Marker(
                                        location=[lat, lng],
                                        popup=selected_type,
                                        tooltip=f"{idx}. {selected_type} - {name}",
                                        icon=folium.Icon(color='orange')
                                    ).add_to(destinationMap)

                                    # Extracting opening hours
                                    opening_hours = POI.get('opening_hours', {}).get('weekday_text', 'N/A')

                                    # st.write(f"- {name} ({r_type}): Rating - {rating}, Price Level - {price_level}")

                                    # Append data to DataFrame
                                    POI_df = pd.DataFrame([{
                                        'Name': name,
                                        'Type': r_type,
                                        'Price Level': price_level,
                                        'Rating': rating,
                                        'Opening Hours': opening_hours,
                                        'lat': lat,
                                        'lng': lng

                                    }])

                                    # Add the DataFrame to the list
                                    POI_dfs.append(POI_df)

                                # Concatenate the list of DataFrames into a single DataFrame
                                POI_df = pd.concat(POI_dfs, ignore_index=True)

                            else:
                                st.warning("No Google Maps Api locations found nearby.")





                        if visaTripadvisorHotel: ################################
                            url = "https://tripadvisor-scraper.p.rapidapi.com/hotels/list"

                            #Ortseingabe = st.text_input("Ort eingeben", value=LegEndLocation)

                            querystring = {"query": LegEndLocation, "page": "1"}

                            headers = {
                                "x-rapidapi-key": X_RapidAPI_Key,
                                "x-rapidapi-host": "tripadvisor-scraper.p.rapidapi.com"
                            }

                            response = requests.get(url, headers=headers, params=querystring)

                            # st.write(response.json())

                            if response.status_code == 200:
                                data = response.json()

                                # Extract the list of hotels
                                hotels = data.get('results', [])

                                # Create a DataFrame
                                df = pd.DataFrame(hotels)

                                # Only keep relevant columns
                                df = df[["name", "link", "reviews", "rating", "price_range_usd", "phone", "address",
                                         "ranking", "latitude", "longitude"]]

                                # Normalize nested JSON columns
                                df["min_price"] = df["price_range_usd"].apply(
                                    lambda x: x.get('min') if isinstance(x, dict) else None)
                                df["max_price"] = df["price_range_usd"].apply(
                                    lambda x: x.get('max') if isinstance(x, dict) else None)
                                df["rank"] = df["ranking"].apply(
                                    lambda x: x.get('current_rank') if isinstance(x, dict) else None)
                                df["total_rank"] = df["ranking"].apply(
                                    lambda x: x.get('total') if isinstance(x, dict) else None)

                                # Drop columns
                                df = df.drop(columns=["price_range_usd", "ranking", "rank","total_rank"])

                                # Reorder columns to move 'link' to the far right
                                cols = [col for col in df.columns if col != "link"] + ["link"]
                                df = df[cols]

                                # Display the DataFrame in Streamlit
                                #st.dataframe(df)

                                # Create a Folium map centered around the first hotel
                                #map_center = [df["latitude"].mean(), df["longitude"].mean()]
                                #folium_map = folium.Map(location=map_center, zoom_start=12)

                                # Add hotel markers with a hotel icon to the map
                                for _, row in df.iterrows():
                                    folium.Marker(
                                        location=[row["latitude"], row["longitude"]],
                                        popup=f"{row['name']}<br>Rating: {row['rating']}<br><a href='{row['link']}' target='_blank'>Hotel Link</a>",
                                        tooltip=row["name"],
                                        icon=folium.Icon(icon="bed", prefix="fa")
                                    ).add_to(destinationMap)

                            else:
                                st.warning("No hotels found.")




                        if visaBookingComHotel: ##########################

                            # API request setup
                            url = "https://booking-com.p.rapidapi.com/v1/hotels/search-by-coordinates"

                            querystring = {
                                "adults_number": numerOfAdultsString,
                                "checkin_date": CheckInDate,
                                "children_number": "1",
                                "locale": "en-gb",
                                "room_number": "1",
                                "units": "metric",
                                "filter_by_currency": "CHF",
                                "longitude": str(last_lon),
                                "children_ages": "5,0",
                                "checkout_date": CheckOutDate,
                                "latitude": str(last_lat),
                                "order_by": "popularity",
                                "include_adjacency": "true",
                                "page_number": "0",
                                "categories_filter_ids": "class::2,class::4,free_cancellation::1"
                            }

                            headers = {
                                "x-rapidapi-key": X_RapidAPI_Key,
                                "x-rapidapi-host": "booking-com.p.rapidapi.com"
                            }

                            # Send the request
                            response = requests.get(url, headers=headers, params=querystring)

                            #st.info(response.status_code)

                            if response.status_code == 200:

                                # Extract JSON data
                                data = response.json()

                                # Extract the required information for each hotel
                                hotels = data.get("result", [])

                                if (len(hotels)) ==0:
                                    st.warning("Found no available hotels on booking.com")

                                if (len(hotels)) >0:
                                    # Define the columns and extract data
                                    hotel_data = []
                                    for hotel in hotels:
                                        hotel_info = {
                                            "hotel_name": hotel.get("hotel_name"),
                                            "address": hotel.get("address"),
                                            "min_total_price": hotel.get("min_total_price"),
                                            "address_trans": hotel.get("address_trans"),
                                            "city_name_en": hotel.get("city_name_en"),
                                            "url": hotel.get("url"),
                                            "city": hotel.get("city"),
                                            "distance": hotel.get("distance"),
                                            "review_score": hotel.get("review_score"),
                                            "review_score_word": hotel.get("review_score_word"),
                                            "latitude": hotel.get("latitude"),
                                            "longitude": hotel.get("longitude"),

                                        }
                                        hotel_data.append(hotel_info)

                                    # Convert to DataFrame
                                    df = pd.DataFrame(hotel_data)

                                    # Reorder the columns to have "hotel_name" as the first column
                                    df = df[[
                                        "hotel_name",
                                        "address",
                                        "min_total_price",
                                        "address_trans",
                                        "city_name_en",
                                        "url",
                                        "city",
                                        "distance",
                                        "review_score",
                                        "review_score_word",
                                        "latitude",
                                        "longitude"
                                    ]]

                                    df.sort_values(by='distance', ascending=True)

                                    # Display the DataFrame using Streamlit
                                    #st.write(df)

                                    # Create a Folium map centered around the average coordinates
                                    #map_center = [df['latitude'].mean(), df['longitude'].mean()]
                                    #mymap = folium.Map(location=map_center, zoom_start=12)

                                    # Add markers to the map
                                    # marker_cluster = MarkerCluster().add_to(mymap)

                                    for index, row in df.iterrows():
                                        # Create a popup with the hotel name and other details
                                        # popup_text = f"<b>{row['hotel_name']}</b><br>Price: {row['min_total_price']} AED<br>Review: {row['review_score']} ({row['review_score_word']})"

                                        # Add a marker for each hotel
                                        folium.Marker(
                                            location=[row['latitude'], row['longitude']],
                                            # popup=folium.Popup(popup_text, max_width=300),
                                            popup=f"{row['hotel_name']}<br>Review score: {row['review_score']}<br>Min Price: {row['min_total_price']}<br>Review: {row['review_score_word']}<br><a href='{row['url']}' target='_blank'>Hotel Link</a>",
                                            tooltip=row["hotel_name"],
                                            icon=folium.Icon(icon="hotel", prefix="fa")  # Using Font Awesome hotel icon
                                        ).add_to(destinationMap)

                            else:
                                st.warning("No hotels found.")

                        if visaRoutingtipaByOpenAI and openai_api_key == "":  ######################
                            st.warning("Missing key for ChatOpenAI")

                        if visaRoutingtipaByOpenAI and openai_api_key!="": ##########################

                            client = OpenAI(
                            # This is the default and can be omitted
                            api_key = openai_api_key,)

                            # User input

                            user_input = (LegTransport + " from: " + "\n " + LegStartLocation + "\n " + "to: " + LegEndLocation)


                            prompt_input = pre_Input + user_input

                            # Use ChatGPT to generate a response
                            if user_input:
                                try:
                                    response = client.chat.completions.create(
                                        model="gpt-4o",  # Use GPT-3.5 or GPT-4 (e.g., "gpt-4")
                                        messages=[
                                            {"role": "system", "content": "You are a helpful assistant."},
                                            {"role": "user", "content": prompt_input}
                                        ],
                                        max_tokens=800,  # Adjust the length of the response as needed
                                    )
                                    if response and response.choices:
                                        bot_response = response.choices[0].message.content
                                        st.subheader("")
                                        st.info("Info by ChatOpenAI:")
                                        with st.container(height=300):
                                            st.write(bot_response)
                                    else:
                                        st.warning("OpenAI: I'm sorry, I couldn't generate a response at the moment.")
                                except Exception as e:
                                    st.warning("OpenAI: An error occurred while processing your request.")
                                    st.write("Error Message:", str(e))



                        RouteLegMaps.fit_bounds([Leg_sw, Leg_ne])
                        st_data = st_folium(RouteLegMaps, width=725, key=str(i))

                        with st.expander("Show routing table >>>"):
                            st.write(df_mlsTabelle)

                        if visaTrafficByWaze:
                            # Display the DataFrame in Streamlit
                            st.warning("Traffic Alerts Data")
                            # Drop columns
                            traffic_df = traffic_df.drop(columns=["id","timestampUTC"])
                            st.dataframe(traffic_df)



                        # Display the destination map
                        st.info("Stop " + str(Route) + " at "+ LegEndLocation)
                        st_destinationMap = st_folium(destinationMap, width=800)


                        if visaRestaurants:
                            st.subheader("")
                            st.info("Restaurants at Stop " + str(Route) + " in "+ LegEndLocation + "- from Yelp")
                            st.write(restaurant_df)

                        if visaChargingStations:
                            st.subheader("")
                            st.info("Chargers at Stop " + str(Route) + " in "+ LegEndLocation)
                            st.write(charging_station_df)

                        if len(POI_df) > 1:
                            st.info(f"{selected_type}" + "s" + " at Stop " + str(Route) + " in "+ LegEndLocation + " - by Google Maps Api")
                            st.dataframe(POI_df)
                        if len(POI_df) == 1:
                            st.info(f"{selected_type}" + " at Stop " + str(Route) + " in "+ LegEndLocation + " - by Google Maps Api")
                            st.dataframe(POI_df)

                        if visaTripadvisorHotel:
                            st.subheader("")
                            st.info("Hotels at Stop " + str(Route) + " around "+ LegEndLocation)
                            st.dataframe(
                                df,
                                column_config={
                                    "link": st.column_config.LinkColumn()
                                }
                            )


                        if visaBookingComHotel: ##########################
                            st.subheader("")
                            st.info("Hotels at Stop " + str(Route) + " in "+ LegEndLocation)
                            st.dataframe(
                                df,
                                column_config={
                                    "url": st.column_config.LinkColumn()
                                }
                            )



                        if visaWiki:

                            wiki_info1 = scrape_wikipedia(LegEndLocation)
                            if wiki_info1 == None:
                                st.info("Found no Info an Wikipedia")
                            if wiki_info1 != None:
                                st.subheader("")
                                st.info("Info from Wikipedia about " + LegEndLocation)
                                #with st.container():
                                with st.container(height=300):
                                    st.markdown(wiki_info1)


                        st.divider()


                        sumDistance = df_mlsTabelle['distance'].sum() / 1000
                        sumTime = df_mlsTabelle['time'].sum() / 60

                        OverviewSumDistance = OverviewSumDistance + sumDistance
                        OverviewSumTime = OverviewSumTime + sumTime



                    else:
                        st.error(f"API response does not contain 'features' key for points along the route.")
                except Exception as e:
                    st.error(f"An error occurred while processing the API response: {e}")
            else:
                st.error(f"API request failed with status code {response.status_code} for points along the route.")



        if len(result_df)>2:
            st.subheader("Overview of the whole Route")
            sw = result_df[['Latitude', 'Longitude']].min().values.tolist()
            ne = result_df[['Latitude', 'Longitude']].max().values.tolist()
            RouteOverViewMap.fit_bounds([sw, ne])
            st_data = st_folium(RouteOverViewMap, width=725)


            Overviewcol1, Overviewcol2 = st.columns(2)

            Overviewcol1.metric(label="Sum - Distance (km)", value=OverviewSumDistance.round(0))

            if sumTime < 180:
                Overviewcol2.metric(label="Sum - Duration (min)", value=OverviewSumTime.round(0))
            else:
                OverviewSumTime = OverviewSumTime / 60
                Overviewcol2.metric(label="Sum - Duration (hours)", value=OverviewSumTime.round(0))
