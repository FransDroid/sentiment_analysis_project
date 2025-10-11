import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Social Media APIs
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'SentimentAnalysis/1.0')

    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

    # Database
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = 'sentiment_analysis'

    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))  # Use port 5001 by default

    # Processing Settings
    BATCH_SIZE = 100
    UPDATE_INTERVAL = 30  # seconds
    MAX_POSTS_PER_DAY = 1000

    # Keywords to track
    DEFAULT_KEYWORDS = ['python', 'AI', 'machine learning']