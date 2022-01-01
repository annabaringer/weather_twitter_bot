import tweepy, logging, requests, json, random, shutil, os, ssl
import pandas as pd
from time import sleep
from bing_image_downloader import downloader

def authenticate_twitter(logger, consumer_key, consumer_secret, access_token, access_token_secret):
    '''
    Authenticates to twitter. 

        Parameters:
            logger (logger object)
            consumer_key (string): for twitter api
            consumer_secret (string): for twitter api
            access_token (string): for twitter api 
            access_token_secret (string): for twitter api
            
        Returns:
            api: api object already authenticated
    '''

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
    '''
    Reads in the file of cities available from the Open Weather API.

        Parameters:
            json_filename (string): file name of the json file with the city names available
            logger (logger object)
            
        Returns:
            city_dict: dict of cities available for the Open Weather API.
    '''

    try:
        f = open(json_filename)
        city_dict = json.load(f)
        f.close()
    except Exception as e:
        logger.error("Error reading {json_filename}", exc_info=True)
        raise e

    return city_dict


def read_country_crosswalk(filename, logger):
    '''
    Reads in the csv file of county abbrev and their long form english names

        Parameters:
            filename (string): file name of the csv file with the county abbrev and their long form english names
            logger (logger object)
            
        Returns:
            city_dict: pandas dataframe with the country abbreviations and their long forms
    '''

    try:
        # Read in the country codes 
        country_codes = pd.read_csv(filename)
    except Exception as e:
        logger.error("Error reading {filename}", exc_info=True)
        raise e

    return country_codes


def choose_random_city(city_dict):
    '''
    Chooses a random city id to pull the weather from

        Parameters:
            city_dict: the dict of cities available in the Open Weather API
            
        Returns:
            city_id: the randomly choosen city id
            country_code: the country code for the randomly choosen city
    '''

    # Randomly choose a city id
    random_city = random.choice(list(city_dict))

    # Get city id and country
    city_id = random_city['id']
    country_code= random_city['country']

    return city_id, country_code


def get_english_name(crosswalk_filename, country_code, logger):
    '''
    Gets the english name of the country abbreviation from the randomly choosen city. 

        Parameters:
            crosswalk_filename (string): file name of the csv file with the county abbrev and their long form english names
            country_code: the county abbreviation of the randomly choosen city
            logger (logger object)
            
        Returns:
            country_name: the english name of the country of the random city
    '''

    # Get the crosswalk of country code to english name 
    country_codes = read_country_crosswalk(crosswalk_filename, logger)

    # Figure out the english name for the country 
    country_name = country_codes.loc[country_codes['Alpha-2 code'] == country_code, 'English short name lower case'].iloc[0]

    return country_name


def get_weather_data(city_id, weather_api_key, country_name):
    '''
    Gets the weather of the randomly choosen city id. 

        Parameters:
            city_id (string): file name of the csv file with the county abbrev and their long form english names
            weather_api_key (string): the api key for the Open Weather API
            country_name (string): the english country name of the randomly choosen city 
            
        Returns:
            tweet_string (string): the sentence to be tweeted 
            weather_main (string): the main description of the weather (eg. rain, snow, clouds)
            weather_name (string): the name of the city with the random weather 
    '''

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

        # Decide which emoji to use in the tweet
        if weather_main.lower()=='thunderstorm':
            emoji = '\U000026A1'
        elif weather_main.lower()=='drizzle' or weather_main=='rain':
            emoji = '\U00002614'
        elif weather_main.lower()=='snow':
            emoji = '\U00002744'
        elif weather_main.lower()=='clear':
            emoji = '\U00002600'
        elif weather_main.lower()=='clouds':
            emoji = '\U000026C5'
        else:
            emoji = '\U0001F301'

    tweet_string=f'It is {weather_temp}F in {weather_name}, {country_name} {emoji}! With {weather_desc} and {weather_humidity}% humidity, it feels like {weather_feelslike}F.'

    return tweet_string, weather_desc, weather_name


def get_photos(weather_desc, city_name, country_name, api, logger):
    '''
    Determines which photos to tweet out with the weather. Scrapes 3 pictures of the city from Bing.
    Adds one pre-determined picture based on the weather description.

        Parameters:
            weather_desc (string): the description of the weather (eg. rain, snow, clouds)
            city_name (string): the name of the city
            country_name (string): the english country name of the randomly choosen city 
            api: api object already authenticated
            logger (logger object)

        Returns:
            media_ids (list): list of media strings already formatted with twitter api
            successful_images (boolean): flag for if images were succesfully downloaded from Bing
    '''

    # Determine which picture to tweet for the weather
    downloader.download(f'{weather_desc}', limit=1,  output_dir='images', adult_filter_off=False, force_replace=False)

    # Scrape three pictures of the location
    downloader.download(f'{city_name} {country_name}', limit=3,  output_dir='images', adult_filter_off=False, force_replace=False)

    # Make sure it downloaded 3 images of city and 1 of weather 
    city_pics = os.listdir(f'images/{city_name} {country_name}')
    weather_pic = os.listdir(f'images/{weather_desc}')

    if len(city_pics)==3 and len(weather_pic)==1:
        successful_images=True

        logger.info(f"Successful image download for {city_name} {country_name}", exc_info=True)

    pics = [f'images/{city_name} {country_name}/{file}' for file in city_pics]
    pics += [f'images/{weather_desc}/{file}' for file in weather_pic]
    media_ids = [api.media_upload(i).media_id_string for i in pics] 

    return media_ids, successful_images
    
def main():
    # Set the environ variables
    consumer_key = os.environ['consumer_key']
    consumer_secret = os.environ['consumer_secret']
    access_token = os.environ['access_token']
    access_token_secret = os.environ['access_token_secret']
    weather_api_key = os.environ['weather_api_key']
    

    ssl._create_default_https_context = ssl._create_unverified_context

    # Create a logger
    logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO)

    # Authenticate to Twitter
    api = authenticate_twitter(logger, consumer_key, consumer_secret, access_token, access_token_secret)

    # Read in the list of cities available from the api
    city_dict = read_cities('data/city.list.json', logger)

    # Flag to keep track of successful pic download 
    successful_images = False

    while successful_images==False:
        # Choose a random city
        city_id, country_code = choose_random_city(city_dict)

        # Get the english name of the country
        country_name = get_english_name('data/wikipedia-iso-country-codes.csv', country_code, logger)

        # Make the tweet string with weather data
        tweet_string, weather_main, city_name = get_weather_data(city_id, weather_api_key, country_name)

        logger.info(f"Generating tweets for {city_name} {country_name}", exc_info=True)

        # Get photos for the tweet
        media_ids, successful_images = get_photos(weather_main, city_name, country_name, api, logger)

        # Generate tweet with media 
        api.update_status(status=tweet_string, media_ids=media_ids)

        logger.info(f"Cleaning up images for {city_name} {country_name}", exc_info=True)

        # Clean up the images
        shutil.rmtree(f'images/{city_name} {country_name}')

if __name__ == "__main__":
   main()