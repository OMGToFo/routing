#2024.05.07 update wikipedia scrape

import streamlit as st
import requests
import pandas as pd

import folium

from streamlit_folium import st_folium


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

#wikipedia info
import requests
from bs4 import BeautifulSoup

POI_df = pd.DataFrame()


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


def get_lat_long_from_actual_address(Actual_address):
   locator = Nominatim(user_agent='thomasActualAdress')
   Actual_addresslocation = locator.geocode(Actual_address)

   return str(Actual_addresslocation.latitude) +"," + str(Actual_addresslocation.longitude)


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


#Function to fetch location info from Wikipedia ################################
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








st.title("Simple Routing")




######  get location #################################

loc = get_geolocation()
if loc:
   #gelocExpander = st.expander("Show geolocation data of your location:")
   #with gelocExpander:
      #st.write(f"Your coordinates are {loc}")

   lat_actual = loc['coords']['latitude']
   long_actual = loc['coords']['longitude']

   actualLocation = (lat_actual, long_actual)
   # Initialize Nominatim API
   geolocator = Nominatim(user_agent="actualLocationAdress")

   # Get the location (address)
   ActuallocationAdress = geolocator.reverse(actualLocation, exactly_one=True)
    
   # Extract the address
   Actualaddress = ActuallocationAdress.address
   # Output the address
   #st.write(f"The address detected for yor location is: {Actualaddress}")

   #st.write("actualLocation:", actualLocation)

   StartAddress = st.text_input("Start",value=Actualaddress)
   if StartAddress != Actualaddress:
       st.write("Startadresse changed")
       try:
          actualLocation = get_lat_long_from_actual_address(StartAddress)
          st.write("actualLocation: ",actualLocation)
          lat_actual = Actual_addresslocation.latitude
          long_actual = Actual_addresslocation.longitude
       except:
           st.warning("Did not find the location, enter another start address")
           st.stop()





address = st.text_input("Enter Destination Address")
if address:
   try:
      DestinationLocation = get_lat_long_from_address(address)
   except:
      st.warning("Did not find the location of the destination, enter another address")
      st.stop()



   if DestinationLocation and loc: ###########################################



      routingAuswahl = ['drive', 'truck', 'bicycle', 'walk']


      routingModeSelection = st.selectbox("Choose routing",routingAuswahl)



      url = "https://route-and-directions.p.rapidapi.com/v1/routing"

      querystring = {"waypoints":f"{str(lat_actual)},{str(long_actual)}|{DestinationLocation}","mode":routingModeSelection}

      headers = {
          "X-RapidAPI-Key": X_RapidAPI_Key,
          "X-RapidAPI-Host": "route-and-directions.p.rapidapi.com"
      }

      response = requests.get(url, headers=headers, params=querystring)

      #routeDetailsExpander = st.expander("Show json routeinfo")
      #with routeDetailsExpander:
      #   st.write(response.json())





   import folium
   def create_map(response): #routingmap
      # use the response
      mls = response.json()['features'][0]['geometry']['coordinates']
      #st.write(mls)
      points = [(i[1], i[0]) for i in mls[0]]
      m = folium.Map()
      # add marker for the start and ending points
      for point in [points[0], points[-1]]:
         folium.Marker(point).add_to(m)
      # add the lines
      folium.PolyLine(points, weight=5, opacity=1).add_to(m)
      # create optimal zoom
      df = pd.DataFrame(mls[0]).rename(columns={0:'Lon', 1:'Lat'})[['Lat', 'Lon']]
      #st.write(df)
      sw = df[['Lat', 'Lon']].min().values.tolist()
      ne = df[['Lat', 'Lon']].max().values.tolist()
      m.fit_bounds([sw, ne])
      return m

   m = create_map(response)

   st.divider()

   st.info("Show Information about the Destination")


   togglecol1, togglecol2, togglecol3 = st.columns(3)
   visaWiki = togglecol1.toggle("Show Wikipedia Information", value=False, key="hej wiki")
   visaRestaurants = togglecol2.toggle("Show restaurants by Yelp")
   visaChargingStations = togglecol3.toggle("Show Charging Stations", value=False, key="hej igen")

   visaGooglePOI = st.toggle("Show POIs by Google", value=False, key="hey Google")
   if visaGooglePOI:
      eingabeCol1, eingabeCol2 = st.columns([1, 4])

      radiusEingabe = eingabeCol1.number_input("Radius (km)", value=5)
      radiusEingabe = radiusEingabe * 1000

      # Create a select box for the user to choose from the list
      selected_type = eingabeCol2.selectbox("Choose a type", typeList)




   #thomastestar

   thomasLatLonTabelle = response.json()['features'][0]['geometry']['coordinates']
   points = [(i[1], i[0]) for i in thomasLatLonTabelle[0]]

   st.divider()

   df_thomasLatLonTabelle = pd.DataFrame(thomasLatLonTabelle[0]).rename(columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]

   last_lat = df_thomasLatLonTabelle['Lat'].iloc[-1]
   last_lon = df_thomasLatLonTabelle['Lon'].iloc[-1]

   #st.write(last_lon)
   #st.write(last_lat)


   mlsTabelle = response.json()['features'][0]['properties']['legs'][0]['steps']
   df_mlsTabelle = pd.json_normalize(mlsTabelle) #.rename(columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]

   st.write(df_mlsTabelle)

   drivingInstructionAsText = df_mlsTabelle['instruction.text'].to_string(index=False)



   col1, col2 = st.columns(2)

   sumDistance = df_mlsTabelle['distance'].sum()/1000

   #st.write("sumDistance (km):",sumDistance )

   col1.metric(label="Distance (km)", value=sumDistance.round(0))

   sumTime = df_mlsTabelle['time'].sum()/60

   if sumTime < 180:
      col2.metric(label="Duration (min)", value=sumTime.round(0))
   else:
      sumTime = sumTime/60
      col2.metric(label="Duration (hours)", value=sumTime.round(0))

   #st.write("sumTime (min)",sumTime)



   st.info(drivingInstructionAsText)


   # Prepare a map centered around the destination
   destinationMap = folium.Map(location=[last_lat, last_lon], zoom_start=13)
   folium.Marker(
      [last_lat, last_lon], popup="Destination", tooltip="Destination"
   ).add_to(destinationMap)





   if visaRestaurants: #by yelp
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



      # Add markers for each restaurant
      for i, row in restaurant_df.iterrows():
         folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"{row['Name']} - Rating: {row['Rating']}",
            icon=folium.Icon(color='red'),
            tooltip=f"{row['Name']} - {row['Category']} - Rating: {row['Rating']}",
         ).add_to(destinationMap)



   if visaChargingStations:
      map_center = (last_lat, last_lat)

      # Get nearby EV charging stations
      charging_stations = get_nearby_charging_stations(last_lat, last_lon)

      # alle infos vom api st.write(charging_stations)

      # Create a Pandas DataFrame to store charging station information
      charging_station_df = pd.DataFrame({
         'Name': [station['AddressInfo']['Title'] for station in charging_stations],
         'Location': [f"{station['AddressInfo']['AddressLine1']}, {station['AddressInfo']['Town']}" for
                      station in charging_stations],
         'Latitude': [station['AddressInfo']['Latitude'] for station in charging_stations],
         'Longitude': [station['AddressInfo']['Longitude'] for station in charging_stations],
         'Distance': [station['AddressInfo']['Distance'] for station in charging_stations],
         'KW': [station['Connections'][0]['PowerKW'] for station in charging_stations],
         # 'Operational': [station['Connections'][0]['StatusType'] for station in charging_stations],
         'AccessComments': [station['AddressInfo']['AccessComments'] for station in charging_stations],
         # 'AccessComments': [station['AddressInfo']['AccessComments'] for station in charging_stations],
         # 'ID_Test': [station['Connections'][0]['StatusType']['ID'] for station in charging_stations],
      })

      charging_station_df.sort_values(by=['Distance'], inplace=True)

      #charging_map = folium.Map(location=map_center, zoom_start=12)

      # Add markers for charging stations
      for i, row in charging_station_df.iterrows():
         folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"{row['Name']}\n{row['Location']}\n - KW: {row['KW']}",
            tooltip=f"{row['Name']}\n{row['Location']}\n  - KW:  {row['KW']}",
            icon=folium.Icon(color='green', icon='plug')  # Green marker for charging stations
         ).add_to(destinationMap)









   if visaWiki:
      #get_location_info(last_lat, last_lon)
      from geopy.geocoders import Nominatim

      geolocator = Nominatim(user_agent="thomastestarLatLongTillOrt")
      location = geolocator.reverse([last_lat, last_lon])
      #Extract town or village if available
      address_components = location.raw.get('address', {})
      if 1 ==1:
       town = address_components.get('town')
       village = address_components.get('village')
       county = address_components.get('county')
       state = address_components.get('state')

       if town:
           st.write("Town:", town)
           wiki_info = scrape_wikipedia(town)
           st.write(wiki_info)

       elif village:
           st.write("Village:", village)
           wiki_info = scrape_wikipedia(village)
           st.write(wiki_info)

           if wiki_info == None:
               st.write("county:", county)
               wiki_info_county = scrape_wikipedia(county)
               st.write(wiki_info_county)

               if wiki_info_county == None:
                   st.write("state:", state)
                   wiki_info_state = scrape_wikipedia(state)
                   st.write(wiki_info_state)

       else:
           st.write("No town or village found on Wikipedia.")








   ########### Fetch POI Data from Google API ###############################

   if visaGooglePOI:



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

   # Display the routing map ######################
   st.info("Route")
   st_routingMap = st_folium(m, width=800)

   st.info("Destination")

   #Display the destination map
   st_destinationMap = st_folium(destinationMap, width=800)

   # Display DataFrame
   # st.write("\n**Information DataFrame:**")
   if len(POI_df) > 1:
      st.subheader(f"{selected_type}" + "s" + " at Destination - by Google Maps Api")
      st.dataframe(POI_df)
   if len(POI_df) == 1:
      st.subheader(f"{selected_type}" + " at Destination - by Google Maps Api")
      st.dataframe(POI_df)

   if visaRestaurants:
      st.subheader("")
      st.subheader("Restaurants at Destination - from Yelp")
      st.write(restaurant_df)

   if visaChargingStations:
      st.subheader("")
      st.subheader("Chargers at Destination")
      st.write(charging_station_df)



