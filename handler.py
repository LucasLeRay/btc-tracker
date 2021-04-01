import os
import requests
import tweepy
import boto3
from datetime import date

BINANCE_KEY = os.environ.get('BINANCE_KEY')
BINANCE_SECRET = os.environ.get('BINANCE_SECRET')
TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
PHONE_NUMBER = os.environ.get('PHONE_NUMBER')

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_client = tweepy.API(auth)

comprehend = boto3.client('comprehend')
sns = boto3.client('sns')

def notify(currentValue, yesterdayValue, positive, negative, neutral):
    today = date.today().strftime('%d/%m/%Y')
    evolution = '↗️' if currentValue > yesterdayValue else '↘️'
    currentPrice = round(float(currentValue))
    message = f"""
BTC/USD - {today}:
Current: ${currentPrice}{evolution}
🙂: {positive:.0%}
🙁: {negative:.0%}
😐: {neutral:.0%}
    """
    sns.publish(PhoneNumber=PHONE_NUMBER, Message=message)
    print('Phone {} notified.'.format(PHONE_NUMBER))

def getSentiments():
    tweets = tweepy \
        .Cursor(twitter_client.search, q='bitcoin', language='en') \
        .items(100)
    tweets_list = [tweet.text for tweet in tweets]

    positive = []
    negative = []
    neutral = []
    for tweet in tweets_list:
        sentiment = comprehend.detect_sentiment(Text=tweet, LanguageCode='en')['SentimentScore']
        positive.append(sentiment['Positive'])
        negative.append(sentiment['Negative'])
        neutral.append(sentiment['Neutral'])
    sentiments = {
        'positive': sum(positive) / len(positive),
        'negative': sum(negative) / len(negative),
        'neutral': sum(neutral) / len(neutral)
    }
    print('Sentiments:', sentiments)
    return sentiments

def getTicker():
    params = {'symbol': 'BTCUSDT'}
    r = requests.get('https://api.binance.com/api/v3/ticker/24hr', params=params)
    ticker = r.json()
    print('Ticker:', ticker)
    return ticker

def btcTracker(event, context):
    ticker = getTicker()
    sentiments = getSentiments()
    notify( \
        currentValue=ticker['lastPrice'], \
        yesterdayValue=ticker['prevClosePrice'], \
        positive=sentiments['positive'], \
        negative=sentiments['negative'], \
        neutral=sentiments['neutral'] \
    )
    return 'ok'
