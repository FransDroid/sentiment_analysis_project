from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config.settings import Config

class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.DATABASE_NAME]
            # Test connection
            self.client.admin.command('ping')
            logging.info("Connected to MongoDB successfully")
            self.setup_indexes()
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def setup_indexes(self):
        """Set up database indexes for better performance"""
        try:
            # Raw posts collection indexes
            self.db.raw_posts.create_index([("platform", ASCENDING), ("created_at", DESCENDING)])
            self.db.raw_posts.create_index([("keywords", ASCENDING)])
            self.db.raw_posts.create_index([("collected_at", DESCENDING)])

            # Sentiment results collection indexes
            self.db.sentiment_results.create_index([("platform", ASCENDING), ("created_at", DESCENDING)])
            self.db.sentiment_results.create_index([("sentiment.label", ASCENDING)])
            self.db.sentiment_results.create_index([("processed_at", DESCENDING)])

            logging.info("Database indexes created successfully")
        except Exception as e:
            logging.error(f"Error creating indexes: {e}")

    def insert_raw_posts(self, posts: List[Dict]) -> List:
        """Insert raw social media posts"""
        try:
            if posts:
                result = self.db.raw_posts.insert_many(posts)
                logging.info(f"Inserted {len(result.inserted_ids)} raw posts")
                return result.inserted_ids
        except Exception as e:
            logging.error(f"Error inserting raw posts: {e}")
        return []

    def insert_sentiment_results(self, results: List[Dict]) -> List:
        """Insert sentiment analysis results"""
        try:
            if results:
                # Add processing timestamp
                for result in results:
                    result['processed_at'] = datetime.now()

                result = self.db.sentiment_results.insert_many(results)
                logging.info(f"Inserted {len(result.inserted_ids)} sentiment results")
                return result.inserted_ids
        except Exception as e:
            logging.error(f"Error inserting sentiment results: {e}")
        return []

    def get_recent_posts(self, platform: Optional[str] = None, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get recent posts from the database"""
        try:
            query = {}
            if platform:
                query['platform'] = platform

            # Get posts from last N hours
            since = datetime.now() - timedelta(hours=hours)
            query['created_at'] = {'$gte': since}

            posts = list(self.db.raw_posts.find(query)
                        .sort('created_at', DESCENDING)
                        .limit(limit))

            return posts
        except Exception as e:
            logging.error(f"Error getting recent posts: {e}")
            return []

    def get_sentiment_summary(self, platform: Optional[str] = None, hours: int = 24) -> Dict:
        """Get sentiment summary statistics"""
        try:
            match_stage = {}
            if platform:
                match_stage['platform'] = platform

            # Get sentiment data from last N hours
            since = datetime.now() - timedelta(hours=hours)
            match_stage['processed_at'] = {'$gte': since}

            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': '$sentiment.label',
                    'count': {'$sum': 1}
                }}
            ]

            results = list(self.db.sentiment_results.aggregate(pipeline))

            # Convert to percentage
            total = sum(item['count'] for item in results)
            summary = {'positive': 0, 'neutral': 0, 'negative': 0, 'total': total}

            for item in results:
                label = item['_id']
                percentage = (item['count'] / total * 100) if total > 0 else 0
                summary[label] = round(percentage, 2)

            return summary

        except Exception as e:
            logging.error(f"Error getting sentiment summary: {e}")
            return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

    def get_trend_data(self, platform: Optional[str] = None, days: int = 7) -> List[Dict]:
        """Get sentiment trend data over time"""
        try:
            match_stage = {}
            if platform:
                match_stage['platform'] = platform

            # Get data from last N days
            since = datetime.now() - timedelta(days=days)
            match_stage['processed_at'] = {'$gte': since}

            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': {
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$processed_at'}},
                        'hour': {'$hour': '$processed_at'},
                        'sentiment': '$sentiment.label'
                    },
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id.date': 1, '_id.hour': 1}}
            ]

            results = list(self.db.sentiment_results.aggregate(pipeline))
            return results

        except Exception as e:
            logging.error(f"Error getting trend data: {e}")
            return []

    def get_top_posts(self, sentiment: str, platform: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get top posts by sentiment"""
        try:
            query = {'sentiment.label': sentiment}
            if platform:
                query['platform'] = platform

            posts = list(self.db.sentiment_results.find(query)
                        .sort([('sentiment.confidence', DESCENDING), ('processed_at', DESCENDING)])
                        .limit(limit))

            return posts

        except Exception as e:
            logging.error(f"Error getting top posts: {e}")
            return []

    def cleanup_old_data(self, days: int = 30):
        """Remove old data to save storage space"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # Remove old raw posts
            raw_result = self.db.raw_posts.delete_many({'collected_at': {'$lt': cutoff_date}})
            logging.info(f"Deleted {raw_result.deleted_count} old raw posts")

            # Remove old sentiment results
            sentiment_result = self.db.sentiment_results.delete_many({'processed_at': {'$lt': cutoff_date}})
            logging.info(f"Deleted {sentiment_result.deleted_count} old sentiment results")

        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")

    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed")