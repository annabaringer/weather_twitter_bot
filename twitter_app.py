import tweepy, logging, requests, json, random
import pandas as pd
from time import sleep
from os import environ
from bing_image_downloader import downloader
import shutil

def authenticate_twitter(logger, consumer_key, consumer_secret, access_token, access_token_secret):
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


def read_cities(json_filename, logger):
    try:
        f = open(json_filename)
        city_dict = json.load(f)
        f.close()
    except Exception as e:
        logger.error("Error reading {json_filename}", exc_info=True)
        raise e

    return city_dict


def read_country_crosswalk(filename, logger):
    try:
        # Read in the country codes 
        country_codes = pd.read_csv(filename)
    except Exception as e:
        logger.error("Error reading {filename}", exc_info=True)
        raise e

    return country_codes


def choose_random_city(city_dict):
    # Randomly choose a city id
    random_city = random.choice(list(city_dict))

    # Get city id and country
    city_id = random_city['id']
    country_code= random_city['country']

    return city_id, country_code


def get_english_name(crosswalk_filename, country_code, logger):
    # Get the crosswalk of country code to english name 
    country_codes = read_country_crosswalk(crosswalk_filename, logger)

    # Figure out the english name for the country 
    country_name = country_codes.loc[country_codes['Alpha-2 code'] == country_code, 'English short name lower case'].iloc[0]

    return country_name


def get_weather_data(city_id, weather_api_key, country_name):
    # Get current weather 
    complete_url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={weather_api_key}&units=imperial"
    
    # Set a flag to keep track of a successful weather grab
    successful_weather = False

    while(successful_weather == False):
        # get the data
        response = requests.get(complete_url)

        # Convert to json 
        weather = response.json()

        if weather["cod"] != "404":
            weather_desc = weather['weather'][0]['description']
            weather_temp=weather['main']['temp']
            weather_feelslike=weather['main']['feels_like']
            weather_min=weather['main']['temp_min']
            weather_max=weather['main']['temp_max']
            weather_name=weather['name']
            weather_humidity=weather['main']['humidity']
            weather_main=weather['weather'][0]['main']

            successful_weather = True

    tweet_string=f'It is {weather_temp}F in {weather_name}, {country_name}! With {weather_desc} and {weather_humidity}% humidity, it feels like {weather_feelslike}F.'

    return tweet_string, weather_main, weather_name

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
    api = authenticate_twitter(logger, consumer_key, consumer_secret, access_token, access_token_secret)

    # Read in the list of cities available from the api
    city_dict = read_cities('data/city.list.json', logger)

    while True:
        # Choose a random city
        city_id, country_code = choose_random_city(city_dict)

        # Get the english name of the country
        country_name = get_english_name('data/wikipedia-iso-country-codes.csv', country_code, logger)

        # Make the tweet string with weather data
        tweet_string, weather_main, city_name = get_weather_data(city_id, weather_api_key, country_name)

        # Determine which picture to tweet for the weather
        if weather_main == 'Thunderstorm':
            image_path = 'images/thunder.jpg'
        elif weather_main == 'Drizzle':
            image_path = 'images/drizzle.png' 
        elif weather_main == 'Rain':
            image_path = 'images/rain.jpg' 
        elif weather_main == 'Snow':
            image_path = 'images/snow.png' 
        elif weather_main == 'Clear':
            image_path = 'images/clear.png' 
        elif weather_main == 'Clouds':
            image_path = 'images/cloud.png'
        else:
            # Add picture of mist, have, dust etc.
            image_path = 'images/mist.jpg'

        # Scrape three pictures of the location
        downloader.download(f'{city_name} {country_name}', limit=3,  output_dir='images', adult_filter_off=False, force_replace=False, timeout=60, verbose=True)

        pics = (image_path, f'images/{city_name} {country_name}/Image_1.jpg', f'images/{city_name} {country_name}/Image_2.jpg', f'images/{city_name} {country_name}/Image_3.jpg')
        media_ids = [api.media_upload(i).media_id_string for i in pics] 
        
         # Generate tweet with media 
        api.update_status(status=tweet_string, media_ids=media_ids)

        # Generate tweet with media 
        #status = api.update_status_with_media(filename=image_path, status=tweet_string)

        # Clean up the images
        shutil.rmtree(f'images/{city_name} {country_name}')

        # Pause for a 2 hours
        #sleep(7200)
        sleep(60) # FOR TESTING

if __name__ == "__main__":
   main()