import tweepy
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
from config.settings import Config

class TwitterCollector:
    def __init__(self):
        self.client = tweepy.Client(bearer_token=Config.TWITTER_BEARER_TOKEN)
        self.api = tweepy.API(tweepy.OAuth1UserHandler(
            Config.TWITTER_API_KEY,
            Config.TWITTER_API_SECRET,
            Config.TWITTER_ACCESS_TOKEN,
            Config.TWITTER_ACCESS_TOKEN_SECRET
        ))

    def collect_tweets(self, keywords: List[str], max_results: int = 100) -> List[Dict]:
        """Collect tweets for given keywords with rate limiting protection"""
        tweets_data = []
        max_retries = 3
        backoff_time = 60  # Start with 1 minute backoff

        for attempt in range(max_retries):
            try:
                query = " OR ".join(keywords)
                tweets = tweepy.Paginator(
                    self.client.search_recent_tweets,
                    query=query,
                    max_results=min(max_results, 10),  # Limit to 10 per request to avoid rate limits
                    tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang']
                ).flatten(limit=max_results)

                for tweet in tweets:
                    if tweet.lang == 'en':  # Only English tweets
                        tweet_data = {
                            'id': tweet.id,
                            'text': tweet.text,
                            'created_at': tweet.created_at,
                            'author_id': tweet.author_id,
                            'platform': 'twitter',
                            'likes': tweet.public_metrics.get('like_count', 0),
                            'retweets': tweet.public_metrics.get('retweet_count', 0),
                            'collected_at': datetime.now(),
                            'keywords': keywords
                        }
                        tweets_data.append(tweet_data)

                # If successful, break out of retry loop
                break

            except tweepy.TooManyRequests as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Rate limited. Waiting {backoff_time} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff
                else:
                    logging.error(f"Rate limit exceeded after {max_retries} attempts: {e}")
                    return []
            except Exception as e:
                logging.error(f"Error collecting tweets: {e}")
                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {min(backoff_time, 30)} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(min(backoff_time, 30))
                else:
                    return []

        return tweets_data

    def stream_tweets(self, keywords: List[str]):
        """Stream real-time tweets (for future implementation)"""
        pass