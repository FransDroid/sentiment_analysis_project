from pymongo import MongoClient, ASCENDING, DESCENDING
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from config.settings import Config

class MongoDBClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    def _ensure_utc(self, value: Any) -> Any:
        """Ensure datetime values are timezone-aware in UTC."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    def _as_query_datetime(self, value: datetime) -> datetime:
        """Convert datetime to naive UTC for MongoDB queries."""
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def _normalize_document_dates(self, document: Dict) -> Dict:
        """Normalize all datetime-like fields in a document to UTC."""
        for key, value in list(document.items()):
            if isinstance(value, datetime):
                document[key] = self._ensure_utc(value)
            elif isinstance(value, dict):
                document[key] = self._normalize_document_dates(value)
            elif isinstance(value, list):
                normalized_items = []
                for item in value:
                    if isinstance(item, datetime):
                        normalized_items.append(self._ensure_utc(item))
                    elif isinstance(item, dict):
                        normalized_items.append(self._normalize_document_dates(item))
                    else:
                        normalized_items.append(item)
                document[key] = normalized_items
        return document

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
            self.db.raw_posts.create_index([("run_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.raw_posts.create_index([("platform", ASCENDING), ("created_at", DESCENDING)])
            self.db.raw_posts.create_index([("keywords", ASCENDING)])
            self.db.raw_posts.create_index([("collected_at", DESCENDING)])

            # Sentiment results collection indexes
            self.db.sentiment_results.create_index([("run_id", ASCENDING), ("created_at", DESCENDING)])
            self.db.sentiment_results.create_index([("platform", ASCENDING), ("created_at", DESCENDING)])
            self.db.sentiment_results.create_index([("sentiment.label", ASCENDING)])
            self.db.sentiment_results.create_index([("processed_at", DESCENDING)])

            # Run history collection indexes
            self.db.run_history.create_index([("created_at", DESCENDING)])
            self.db.run_history.create_index([("status", ASCENDING)])

            logging.info("Database indexes created successfully")

        except Exception as e:
            logging.error(f"Error creating indexes: {e}")

    def insert_raw_posts(self, posts: List[Dict], run_id: Optional[str] = None) -> List:
        """Insert raw social media posts
        
        Args:
            posts: List of post dictionaries to insert
            run_id: Optional run ID to associate posts with a specific analysis run
        """
        try:
            if posts:
                normalized_posts = []
                for post in posts:
                    post_copy = post.copy()
                    if run_id:
                        post_copy['run_id'] = run_id
                    normalized_posts.append(self._normalize_document_dates(post_copy))
                result = self.db.raw_posts.insert_many(normalized_posts)
                logging.info(f"Inserted {len(result.inserted_ids)} raw posts")
                return result.inserted_ids
        except Exception as e:
            logging.error(f"Error inserting raw posts: {e}")
        return []

    def insert_sentiment_results(self, results: List[Dict], run_id: Optional[str] = None) -> List:
        """Insert sentiment analysis results
        
        Args:
            results: List of sentiment result dictionaries to insert
            run_id: Optional run ID to associate results with a specific analysis run
        """
        try:
            if results:
                # Add processing timestamp and run_id
                for result in results:
                    result['processed_at'] = datetime.now(timezone.utc)
                    if run_id:
                        result['run_id'] = run_id
                    self._normalize_document_dates(result)

                result = self.db.sentiment_results.insert_many(results)
                logging.info(f"Inserted {len(result.inserted_ids)} sentiment results")
                return result.inserted_ids
        except Exception as e:
            logging.error(f"Error inserting sentiment results: {e}")
        return []

    def create_run_record(self, run_id: str, keywords: List[str], duration_days: float) -> None:
        """Persist a new on-demand analysis run record."""
        try:
            record = {
                "_id": run_id,
                "keywords": keywords,
                "duration_days": duration_days,
                "status": "queued",
                "progress": "Queued",
                "created_at": datetime.now(timezone.utc),
                "started_at": None,
                "completed_at": None,
                "stats": None,
                "raw_posts_count": 0,
                "sentiment_results_count": 0,
                "window_start": None,
                "window_end": None,
                "message": None,
            }
            self.db.run_history.insert_one(record)
        except Exception as e:
            logging.error(f"Error creating run record {run_id}: {e}")
            raise

    def update_run_record(self, run_id: str, **fields) -> None:
        """Update an existing run record."""
        if not fields:
            return

        try:
            update_fields = {}
            for key, value in fields.items():
                if key in {"created_at", "started_at", "completed_at", "window_start", "window_end"} and isinstance(value, datetime):
                    update_fields[key] = value.astimezone(timezone.utc)
                else:
                    update_fields[key] = value

            self.db.run_history.update_one({"_id": run_id}, {"$set": update_fields}, upsert=False)
        except Exception as e:
            logging.error(f"Error updating run record {run_id}: {e}")

    def get_recent_runs(self, limit: int = 20) -> List[Dict]:
        """Fetch recent analysis run records."""
        try:
            cursor = self.db.run_history.find().sort("created_at", DESCENDING).limit(limit)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error fetching recent runs: {e}")
            return []

    def get_run_by_id(self, run_id: str) -> Optional[Dict]:
        """Return a single run record by identifier."""
        try:
            return self.db.run_history.find_one({"_id": run_id})
        except Exception as e:
            logging.error(f"Error fetching run record {run_id}: {e}")
            return None

    def get_recent_posts(self, platform: Optional[str] = None, hours: int = 24, limit: int = 1000,
                         start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None,
                         run_id: Optional[str] = None) -> List[Dict]:
        """Get recent posts from the database
        
        Args:
            platform: Filter by platform (optional)
            hours: Number of hours to look back (used if start_dt/end_dt not provided)
            limit: Maximum number of posts to return
            start_dt: Start datetime for filtering (optional, overrides hours)
            end_dt: End datetime for filtering (optional, overrides hours)
            run_id: Filter by run ID (optional, takes precedence over time-based filtering)
        """
        try:
            query = {}
            if run_id:
                query['run_id'] = run_id
            elif platform:
                query['platform'] = platform

            # Use explicit date range if provided, otherwise use hours
            if start_dt or end_dt:
                date_filter = {}
                if start_dt:
                    date_filter['$gte'] = self._as_query_datetime(start_dt)
                if end_dt:
                    date_filter['$lt'] = self._as_query_datetime(end_dt)
                query['created_at'] = date_filter
            else:
                # Fallback to hours-based filtering
                since = datetime.now(timezone.utc) - timedelta(hours=hours)
                query['created_at'] = {'$gte': self._as_query_datetime(since)}

            posts = list(self.db.raw_posts.find(query)
                        .sort('created_at', DESCENDING)
                        .limit(limit))

            return posts
        except Exception as e:
            logging.error(f"Error getting recent posts: {e}")
            return []

    def get_sentiment_summary(self, platform: Optional[str] = None, hours: int = 24,
                              start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None,
                              keyword: Optional[str] = None, run_id: Optional[str] = None) -> Dict:
        """Get sentiment summary statistics
        
        Args:
            platform: Filter by platform (optional)
            hours: Number of hours to look back (used if start_dt/end_dt not provided)
            start_dt: Start datetime for filtering (optional, overrides hours)
            end_dt: End datetime for filtering (optional, overrides hours)
            keyword: Filter by keyword (optional)
            run_id: Filter by run ID (optional, takes precedence over time-based filtering)
        """
        try:
            match_stage = {}
            if run_id:
                match_stage['run_id'] = run_id
            elif platform:
                match_stage['platform'] = platform
            
            if keyword:
                match_stage['keywords'] = keyword

            # Use explicit date range if provided, otherwise use hours
            if start_dt or end_dt:
                date_filter = {}
                if start_dt:
                    date_filter['$gte'] = self._as_query_datetime(start_dt)
                if end_dt:
                    date_filter['$lt'] = self._as_query_datetime(end_dt)
                match_stage['created_at'] = date_filter
            else:
                # Fallback to hours-based filtering
                since = datetime.now(timezone.utc) - timedelta(hours=hours)
                match_stage['created_at'] = {'$gte': self._as_query_datetime(since)}

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

    def get_trend_data(self, platform: Optional[str] = None, days: int = 7,
                       start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None,
                       keyword: Optional[str] = None, run_id: Optional[str] = None) -> List[Dict]:
        """Get sentiment trend data over time
        
        Args:
            platform: Filter by platform (optional)
            days: Number of days to look back (used if start_dt/end_dt not provided)
            start_dt: Start datetime for filtering (optional, overrides days)
            end_dt: End datetime for filtering (optional, overrides days)
            keyword: Filter by keyword (optional)
            run_id: Filter by run ID (optional, takes precedence over time-based filtering)
        """
        try:
            match_stage = {}
            if run_id:
                match_stage['run_id'] = run_id
            elif platform:
                match_stage['platform'] = platform
            
            if keyword:
                match_stage['keywords'] = keyword

            # Use explicit date range if provided, otherwise use days
            if start_dt or end_dt:
                date_filter = {}
                if start_dt:
                    date_filter['$gte'] = self._as_query_datetime(start_dt)
                if end_dt:
                    date_filter['$lt'] = self._as_query_datetime(end_dt)
                match_stage['created_at'] = date_filter
            else:
                # Fallback to days-based filtering
                since = datetime.now(timezone.utc) - timedelta(days=days)
                match_stage['created_at'] = {'$gte': self._as_query_datetime(since)}

            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': {
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}},
                        'hour': {'$hour': '$created_at'},
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

    def get_top_posts(self, sentiment: str, platform: Optional[str] = None, limit: int = 10,
                      start_dt: Optional[datetime] = None, end_dt: Optional[datetime] = None,
                      keyword: Optional[str] = None, run_id: Optional[str] = None) -> List[Dict]:
        """Get top posts by sentiment
        
        Args:
            sentiment: Sentiment label to filter by ('positive', 'negative', 'neutral')
            platform: Filter by platform (optional)
            limit: Maximum number of posts to return
            start_dt: Start datetime for filtering (optional)
            end_dt: End datetime for filtering (optional)
            keyword: Filter by keyword (optional)
            run_id: Filter by run ID (optional, takes precedence over time-based filtering)
        """
        try:
            query = {'sentiment.label': sentiment}
            if run_id:
                query['run_id'] = run_id
            elif platform:
                query['platform'] = platform
            
            if keyword:
                query['keywords'] = keyword

            # Add date range filtering if provided
            if start_dt or end_dt:
                date_filter = {}
                if start_dt:
                    date_filter['$gte'] = self._as_query_datetime(start_dt)
                if end_dt:
                    date_filter['$lt'] = self._as_query_datetime(end_dt)
                query['created_at'] = date_filter

            posts = list(self.db.sentiment_results.find(query)
                        .sort([('sentiment.confidence', DESCENDING), ('processed_at', DESCENDING)])
                        .limit(limit))

            return posts

        except Exception as e:
            logging.error(f"Error getting top posts: {e}")
            return []

    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed")

    def get_active_keywords(self) -> List[str]:
        """Return default keywords for data collection."""
        try:
            doc = self.db.run_history.find_one({"status": "completed"}, sort=[("created_at", DESCENDING)])
            if doc and doc.get("keywords"):
                return doc["keywords"]
        except Exception as e:
            logging.error(f"Error resolving active keywords from run history: {e}")
        return Config.DEFAULT_KEYWORDS

    def get_sentiment_by_keywords(self, hours: int = 24, 
                                   start_dt: Optional[datetime] = None,
                                   end_dt: Optional[datetime] = None,
                                   run_id: Optional[str] = None) -> List[Dict]:
        """Get sentiment statistics grouped by keyword
        
        Args:
            hours: Number of hours to look back (used if start_dt/end_dt not provided)
            start_dt: Start datetime for filtering (optional)
            end_dt: End datetime for filtering (optional)
            run_id: Filter by run ID (optional, takes precedence over time-based filtering)
            
        Returns:
            List of dicts with keyword, sentiment breakdown, and post count
            Example: [
                {
                    'keyword': 'AI',
                    'positive': 65.5,
                    'neutral': 20.0,
                    'negative': 14.5,
                    'total': 200
                },
                ...
            ]
        """
        try:
            # Build match stage for date filtering
            match_stage = {}
            if run_id:
                match_stage['run_id'] = run_id
            
            if start_dt or end_dt:
                date_filter = {}
                if start_dt:
                    date_filter['$gte'] = self._as_query_datetime(start_dt)
                if end_dt:
                    date_filter['$lt'] = self._as_query_datetime(end_dt)
                match_stage['created_at'] = date_filter
            else:
                since = datetime.now(timezone.utc) - timedelta(hours=hours)
                match_stage['created_at'] = {'$gte': self._as_query_datetime(since)}
            
            # Aggregation pipeline to unwind keywords and group by keyword + sentiment
            pipeline = [
                {'$match': match_stage},
                {'$unwind': '$keywords'},  # Unwind keywords array
                {'$group': {
                    '_id': {
                        'keyword': '$keywords',
                        'sentiment': '$sentiment.label'
                    },
                    'count': {'$sum': 1}
                }},
                {'$group': {
                    '_id': '$_id.keyword',
                    'sentiments': {
                        '$push': {
                            'sentiment': '$_id.sentiment',
                            'count': '$count'
                        }
                    },
                    'total': {'$sum': '$count'}
                }},
                {'$sort': {'total': -1}}  # Sort by most posts
            ]
            
            results = list(self.db.sentiment_results.aggregate(pipeline))
            
            # Format results
            formatted_results = []
            for item in results:
                keyword_data = {
                    'keyword': item['_id'],
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0,
                    'total': item['total']
                }
                
                # Calculate percentages
                for sentiment_info in item['sentiments']:
                    label = sentiment_info['sentiment']
                    count = sentiment_info['count']
                    percentage = (count / item['total'] * 100) if item['total'] > 0 else 0
                    keyword_data[label] = round(percentage, 2)
                
                formatted_results.append(keyword_data)
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error getting sentiment by keywords: {e}")
            return []
    
