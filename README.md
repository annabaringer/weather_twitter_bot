# Twitter Weather Bot

#### Currently tweeting at: https://twitter.com/worldlyweather

Twitter Weather Bot is a twitter bot that tweets the weather and photos of random cities around the world. 

## To Use

You will need Twitter API and Open Weather API credentials. To run locally, I recommend that you create a creds file and import those into `twitter_app.py`.

Here is an example of what your credentials file could look like:
``` 
consumer_key = 'xxxx'
consumer_secret = 'xxxx'
access_token = 'xxxx'
access_token_secret = 'xxxx'
bearer_token = 'xxxx'
weather_api_key = 'xxxx'
```

And then imported into twitter_app.py as: `from creds_file import * `

After your API credentials are set up, you should install the requirements: `pip install -r requirements.txt `

And then you can run the script to tweet once using `python twitter_app.py `.

## How It Works
A random city is selected from the list of cities that are supported from Open Weather's API. Then, Open Weather's API is called to get the current weather. Next, photos of the random city are scraped from Bing. 

The version of the bot running at @worldlyweather on Twitter is deployed on Heroku and is using the Heroku scheduler to tweet at 2.5 hour intervals. 
