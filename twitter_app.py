import tweepy, logging, requests, json, random
import pandas as pd
from time import sleep
from creds import * 


def authenticate_twitter():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    # Make sure the authentication works
    try:
            api.verify_credentials()
    except Exception as e:
            logger.error("Error creating API", exc_info=True)
            raise e
    
    return api

# Create a logger
logger = logging.getLogger()

# Authenticate to Twitter
api = authenticate_twitter()

# Get current weather 

# Read in the list of cities available
f = open('city.list.json')
city_dict = json.load(f)
f.close()

# Read in the country codes 
country_codes = pd.read_csv('wikipedia-iso-country-codes.csv')

# Randomly choose a city id
random_city = random.choice(list(city_dict))

# Get city id and country
city_id = random_city['id']
country_code= random_city['country']

# Figure out the english name for the country 
country_name = country_codes.loc[country_codes['Alpha-2 code'] == country_code, 'English short name lower case'].iloc[0]

 
# base_url variable to store url
complete_url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={weather_api_key}&units=imperial"
 
# get the data
response = requests.get(complete_url)

# convert to json 
weather = response.json()

if weather["cod"] != "404":
    weather_desc = weather['weather'][0]['description']
    weather_temp=weather['main']['temp']
    weather_feelslike=weather['main']['feels_like']
    weather_min=weather['main']['temp_min']
    weather_max=weather['main']['temp_max']
    weather_name=weather['name']
    weather_humidity=weather['main']['humidity']

tweet_string=f'It is {weather_temp}F in {weather_name}, {country_name}! With {weather_desc} and {weather_humidity}% humidity, it feels like {weather_feelslike}F.'

# Create a tweet
api.update_status(tweet_string)

# Pause for a few hours
#sleep(8640)

