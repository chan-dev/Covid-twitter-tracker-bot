import requests
import os
import pandas as pd
import tweepy
from os.path import join, dirname
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import date

dotenv_path = join(dirname("__file__"), '.env')
load_dotenv(dotenv_path)

API_KEY = os.environ.get('API_KEY')
API_KEY_SECRET = os.environ.get('API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')

URL = 'https://www.worldometers.info/coronavirus/#countries'

page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

# scrape required elements
table = soup.find(id='main_table_countries_today')
data = table.find('tbody').select('tr:not(.row_continent)')


def get_headers(table):
    th = table.select('thead th')
    headers = [h.text.strip() for h in th]
    country_index = headers.index('Country,Other')
    headers[country_index] = 'Country'
    return headers


def build_table_dict(headers, data):
    # list comprehension
    columns = [[column, []] for column in headers]

    # exclude first column because it's not useful for our use-case
    # it's the row for "World" data
    for row in data:
        # reset on each iteration
        i = 0  # counter for the header
        cells = row.find_all('td')
        # traverse every data on current row
        for cell in cells:
            # 2nd argument is the array for each header
            columns[i][1].append(cell.text.strip())
            i += 1  # move to the next header
    return columns


def send_tweet(tweet):
    auth = tweepy.OAuthHandler(API_KEY, API_KEY_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth, wait_on_rate_limit=True)
    try:
        api.verify_credentials()
    # update exception handling
    except tweepy.error.TweepError as error:
        print(error)
    else:
        api.update_status(status=tweet)
        print('Tweet has been posted')


def build_tweet(ph_data, world_data):
    # get current date
    cur_date = date.today().strftime('%b %d, %Y')

    return (
        f"#Covid19PH\n{cur_date}\n\n"
        f"Philippines:\n"
        f"  Cases: {ph_data['TotalCases']}\n"
        f"  Active Cases: {ph_data['ActiveCases']}\n"
        f"  New Cases: {ph_data['NewCases']}\n"
        f"  Deaths: {ph_data['TotalDeaths']}\n"
        f"  Recovered: {ph_data['TotalRecovered']}\n"
        f"\n\n"
        f"World:\n"
        f"  Cases: {world_data['TotalCases']}\n"
        f"  Active Cases: {world_data['ActiveCases']}\n"
        f"  New Cases: {world_data['NewCases']}\n"
        f"  Deaths: {world_data['TotalDeaths']}\n"
        f"  Recovered: {world_data['TotalRecovered']}\n"
    )


table_headers = get_headers(table)
table_columns = build_table_dict(table_headers, data)

dataDict = {header: values for (header, values) in table_columns}
df = pd.DataFrame(dataDict)

required_fields = ['Country', 'TotalCases', 'NewCases',
                   'TotalDeaths', 'NewDeaths', 'TotalRecovered', 'ActiveCases']

per_country_data = df.set_index('Country', drop=False)
world_data = per_country_data.loc['World', required_fields]
ph_data = per_country_data.loc['Philippines', required_fields]

tweet = build_tweet(ph_data, world_data)
send_tweet(tweet)
