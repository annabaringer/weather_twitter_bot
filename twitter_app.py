import tweepy, logging, requests, json, random
import pandas as pd
from time import sleep
from creds import * 
from os import environ

def authenticate_twitter(logger):
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


def read_cities(json_filename):
    f = open(json_filename)
    city_dict = json.load(f)
    f.close()

    return city_dict


def read_country_crosswalk(filename):
    # Read in the country codes 
    country_codes = pd.read_csv(filename)

    return country_codes


def choose_random_city(city_dict):
    # Randomly choose a city id
    random_city = random.choice(list(city_dict))

    # Get city id and country
    city_id = random_city['id']
    country_code= random_city['country']

    return city_id, country_code


def get_english_name(crosswalk_filename, country_code):
    # Get the crosswalk of country code to english name 
    country_codes = read_country_crosswalk(crosswalk_filename)

    # Figure out the english name for the country 
    country_name = country_codes.loc[country_codes['Alpha-2 code'] == country_code, 'English short name lower case'].iloc[0]

    return country_name


def get_weather_data(city_id, weather_api_key, country_name):
    # Get current weather 
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

    return tweet_string

def main():
    # Set the environ variables
    consumer_key = environ['consumer_key']
    consumer_secret = environ['consumer_secret']
    access_token = environ['access_token']
    access_token_secret = environ['access_token_secret']
    weather_api_key = environ['weather_api_key']

    # Create a logger
    logger = logging.getLogger()

    # Authenticate to Twitter
    api = authenticate_twitter(logger)

    # Read in the list of cities available from the api
    city_dict = read_cities('city.list.json')

    while True:
        # Choose a random city
        city_id, country_code = choose_random_city(city_dict)

        country_name = get_english_name('wikipedia-iso-country-codes.csv', country_code)

        # Make the tweet with weather data
        tweet_string = get_weather_data(city_id, weather_api_key, country_name)

        # Create a tweet
        api.update_status(tweet_string)

        # Pause for a few hours
        sleep(8640)
        #sleep(60) # FOR TESTING

if __name__ == "__main__":
   main()