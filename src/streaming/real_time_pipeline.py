import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from src.data_collection.twitter_collector import TwitterCollector
from src.data_collection.reddit_collector import RedditCollector
from src.data_collection.youtube_collector import YouTubeCollector
from src.model.sentiment_analysis.sentiment_analyzer import SentimentAnalyzer
from src.database.mongodb_client import MongoDBClient
from .data_processor import DataProcessor
from config.settings import Config

class RealTimePipeline:
    def __init__(self, keywords_source: callable = None):
        self.twitter_collector = TwitterCollector()
        self.reddit_collector = RedditCollector()
        self.youtube_collector = YouTubeCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.db_client = MongoDBClient()
        self.data_processor = DataProcessor()

        self.is_running = False
        self.keywords_source = keywords_source
        self.keywords = Config.DEFAULT_KEYWORDS
        self.update_interval = Config.UPDATE_INTERVAL

        # Thread lock for safe single-cycle execution
        self._lock = threading.Lock()

    def get_keywords(self):
        if self.keywords_source:
            return self.keywords_source()
        return self.db_client.get_active_keywords()

    def keywords_to_subreddits(self, keywords: List[str]) -> List[str]:
        """Convert keywords to subreddit names and add general subreddits"""
        subreddits = set()
        
        # Add general broad subreddits for wider coverage
        general_subreddits = ['technology', 'news', 'todayilearned']
        subreddits.update(general_subreddits)
        
        # Convert each keyword to a potential subreddit name
        for keyword in keywords:
            # Clean and format keyword as subreddit name (remove spaces, special chars)
            cleaned = keyword.strip().replace(' ', '').replace('-', '').replace('_', '')
            if cleaned:
                subreddits.add(cleaned)
        
        logging.info(f"Using subreddits: {list(subreddits)}")
        return list(subreddits)

    def collect_data_from_all_sources(self, start_time: datetime = None, end_time: datetime = None) -> List[Dict]:
        """Collect data from all social media sources in parallel"""
        all_posts = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit collection tasks with increased limits
            twitter_future = executor.submit(
                self.twitter_collector.collect_tweets,
                self.keywords,
                max_results=500
            )

            reddit_future = executor.submit(
                self.reddit_collector.collect_posts,
                self.keywords_to_subreddits(self.keywords),  # Dynamic subreddits from keywords
                self.keywords,
                limit=500
            )

            youtube_future = executor.submit(
                self.youtube_collector.search_videos,
                self.keywords,
                max_results=200
            )

            # Collect results
            try:
                twitter_posts = twitter_future.result(timeout=30)
                twitter_posts = self._filter_posts_by_timeframe(twitter_posts, start_time, end_time)
                all_posts.extend(twitter_posts)
                logging.info(f"Collected {len(twitter_posts)} Twitter posts")
            except Exception as e:
                logging.error(f"Error collecting Twitter data: {e}")

            try:
                reddit_posts = reddit_future.result(timeout=30)
                reddit_posts = self._filter_posts_by_timeframe(reddit_posts, start_time, end_time)
                all_posts.extend(reddit_posts)
                logging.info(f"Collected {len(reddit_posts)} Reddit posts")
            except Exception as e:
                logging.error(f"Error collecting Reddit data: {e}")

            try:
                youtube_videos = youtube_future.result(timeout=30)
                youtube_videos = self._filter_posts_by_timeframe(youtube_videos, start_time, end_time)
                all_posts.extend(youtube_videos)
                logging.info(f"Collected {len(youtube_videos)} YouTube videos")
            except Exception as e:
                logging.error(f"Error collecting YouTube data: {e}")

        return all_posts

    def _filter_posts_by_timeframe(self, posts: List[Dict], start_time: datetime, end_time: datetime) -> List[Dict]:
        if not posts or (start_time is None and end_time is None):
            return posts or []

        filtered = []
        for post in posts:
            created_at = self._extract_timestamp(post)

            if created_at is None:
                filtered.append(post)
                continue

            if start_time and created_at < start_time:
                continue
            if end_time and created_at > end_time:
                continue

            filtered.append(post)

        return filtered

    @staticmethod
    def _extract_timestamp(post: Dict) -> datetime:
        candidate = post.get('created_at') or post.get('collected_at') or post.get('published_at')

        if candidate is None:
            return None

        if isinstance(candidate, datetime):
            if candidate.tzinfo is None:
                return candidate.replace(tzinfo=timezone.utc)
            return candidate.astimezone(timezone.utc)

        if isinstance(candidate, str):
            try:
                dt = datetime.fromisoformat(candidate)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                return None

        return None

    def process_sentiment_batch(self, posts: List[Dict], run_id: Optional[str] = None) -> List[Dict]:
        """Process sentiment analysis for a batch of posts
        
        Args:
            posts: List of posts to analyze
            run_id: Optional run ID to associate results with a specific analysis run
        """
        sentiment_results = []

        try:
            # Use Spark for data preprocessing
            cleaned_posts = self.data_processor.process_batch_data(posts)

            for post in cleaned_posts:
                text = post.get('text', '') or post.get('title', '') or post.get('description', '')

                if text:
                    sentiment = self.sentiment_analyzer.predict_sentiment(text)

                    result = {
                        'post_id': post.get('id'),
                        'platform': post.get('platform'),
                        'text': text,
                        'created_at': post.get('created_at'),
                        'sentiment': sentiment,
                        'keywords': post.get('keywords', []),  # Preserve keywords from raw post
                        'processed_at': datetime.now(),
                        'metadata': {
                            'author_id': post.get('author_id') or post.get('author'),
                            'likes': post.get('likes', 0),
                            'retweets': post.get('retweets', 0),
                            'score': post.get('score', 0)
                        }
                    }
                    if run_id:
                        result['run_id'] = run_id
                    sentiment_results.append(result)

            logging.info(f"Processed sentiment for {len(sentiment_results)} posts")

        except Exception as e:
            logging.error(f"Error processing sentiment batch: {e}")

        return sentiment_results

    def store_results(self, raw_posts: List[Dict], sentiment_results: List[Dict], run_id: Optional[str] = None):
        """Store results in MongoDB
        
        Args:
            raw_posts: List of raw posts to store
            sentiment_results: List of sentiment analysis results to store
            run_id: Optional run ID to associate data with a specific analysis run
        """
        try:
            # Store raw posts
            if raw_posts:
                self.db_client.insert_raw_posts(raw_posts, run_id=run_id)

            # Store sentiment results
            if sentiment_results:
                self.db_client.insert_sentiment_results(sentiment_results, run_id=run_id)

        except Exception as e:
            logging.error(f"Error storing results: {e}")

    def run_single_cycle(self, keywords=None, duration_days=None, run_id: Optional[str] = None):
        """Run one cycle of the pipeline and return summary statistics.
        
        Args:
            keywords: Optional list of keywords to analyze
            duration_days: Optional number of days to look back
            run_id: Optional run ID to associate collected data with a specific analysis run
        """
        original_keywords = self.keywords
        stats = {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}
        raw_posts_count = 0
        sentiment_results_count = 0

        try:
            # Use provided keywords or fall back to config
            if keywords:
                current_keywords = keywords
                logging.info(f"Using custom keywords: {current_keywords}")
            else:
                current_keywords = self.keywords

            # Temporarily override keywords for this cycle
            self.keywords = current_keywords

            logging.info("Starting data collection cycle...")

            window_end = datetime.now(timezone.utc)
            window_start = None
            if duration_days and duration_days > 0:
                window_start = window_end - timedelta(days=duration_days)
                logging.info(
                    "Restricting data collection to window %s - %s",
                    window_start.isoformat(),
                    window_end.isoformat()
                )
            else:
                logging.info("No duration window provided; collecting latest available data")

            # Collect data from all sources (collectors will use self.keywords)
            raw_posts = self.collect_data_from_all_sources(start_time=window_start, end_time=window_end)
            raw_posts_count = len(raw_posts) if raw_posts else 0

            if raw_posts:
                # Process sentiment analysis
                sentiment_results = self.process_sentiment_batch(raw_posts, run_id=run_id)
                sentiment_results_count = len(sentiment_results) if sentiment_results else 0

                # Store results in database
                self.store_results(raw_posts, sentiment_results, run_id=run_id)

                # Generate summary stats
                stats = self.data_processor.aggregate_sentiment_stats(sentiment_results)
                logging.info(f"Cycle completed. Sentiment distribution: {stats}")

            else:
                logging.info("No new posts collected in this cycle")

            return {
                'stats': stats,
                'raw_posts_count': raw_posts_count,
                'sentiment_results_count': sentiment_results_count,
                'time_window': {
                    'start': window_start,
                    'end': window_end
                }
            }

        except Exception as e:
            logging.error(f"Error in pipeline cycle: {e}")
            raise

        finally:
            # Restore original keywords
            self.keywords = original_keywords

    def run_single_cycle_once(self, keywords=None, duration_days=None, run_id: Optional[str] = None):
        """Thread-safe way to run a single cycle ONCE on demand.
        
        Args:
            keywords: Optional list of keywords to analyze
            duration_days: Optional number of days to look back
            run_id: Optional run ID to associate collected data with a specific analysis run
        """
        with self._lock:
            try:
                cycle_result = self.run_single_cycle(keywords=keywords, duration_days=duration_days, run_id=run_id)
                return {"status": "success", **(cycle_result or {})}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def start_streaming(self):
        """Start the real-time streaming pipeline"""
        self.is_running = True
        logging.info("Starting real-time sentiment analysis pipeline...")

        while self.is_running:
            try:
                cycle_start = time.time()

                # Update keywords from source
                self.keywords = self.get_keywords()

                # Run one cycle
                self.run_single_cycle()

                # Calculate sleep time to maintain interval
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, self.update_interval - cycle_duration)

                if sleep_time > 0:
                    logging.info(f"Cycle completed in {cycle_duration:.2f}s. Sleeping for {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                else:
                    logging.warning(f"Cycle took {cycle_duration:.2f}s, longer than interval {self.update_interval}s")

            except KeyboardInterrupt:
                logging.info("Pipeline stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error in pipeline: {e}")
                time.sleep(5)  # Brief pause before retrying

        self.stop_streaming()

    def stop_streaming(self):
        """Stop the streaming pipeline"""
        self.is_running = False
        self.data_processor.stop_spark()
        self.db_client.close_connection()
        logging.info("Streaming pipeline stopped")

    def update_keywords(self, new_keywords: List[str]):
        """Update the keywords being tracked"""
        self.keywords = new_keywords
        logging.info(f"Updated keywords: {self.keywords}")

# Example usage function
def run_pipeline():
    """Function to run the pipeline"""
    pipeline = RealTimePipeline()

    try:
        pipeline.start_streaming()
    except KeyboardInterrupt:
        logging.info("Stopping pipeline...")
        pipeline.stop_streaming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()