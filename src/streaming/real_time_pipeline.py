import threading
import time
import logging
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

from src.data_collection.twitter_collector import TwitterCollector
from src.data_collection.reddit_collector import RedditCollector
from src.data_collection.youtube_collector import YouTubeCollector
from src.sentiment_analysis.sentiment_analyzer import SentimentAnalyzer
from src.database.mongodb_client import MongoDBClient
from .data_processor import DataProcessor
from config.settings import Config

class RealTimePipeline:
    def __init__(self):
        self.twitter_collector = TwitterCollector()
        self.reddit_collector = RedditCollector()
        self.youtube_collector = YouTubeCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.db_client = MongoDBClient()
        self.data_processor = DataProcessor()

        self.is_running = False
        self.keywords = Config.DEFAULT_KEYWORDS
        self.update_interval = Config.UPDATE_INTERVAL

    def collect_data_from_all_sources(self) -> List[Dict]:
        """Collect data from all social media sources in parallel"""
        all_posts = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit collection tasks
            twitter_future = executor.submit(
                self.twitter_collector.collect_tweets,
                self.keywords,
                max_results=50
            )

            reddit_future = executor.submit(
                self.reddit_collector.collect_posts,
                ['python', 'MachineLearning', 'artificial'],  # Example subreddits
                self.keywords,
                limit=50
            )

            youtube_future = executor.submit(
                self.youtube_collector.search_videos,
                self.keywords,
                max_results=20
            )

            # Collect results
            try:
                twitter_posts = twitter_future.result(timeout=30)
                all_posts.extend(twitter_posts)
                logging.info(f"Collected {len(twitter_posts)} Twitter posts")
            except Exception as e:
                logging.error(f"Error collecting Twitter data: {e}")

            try:
                reddit_posts = reddit_future.result(timeout=30)
                all_posts.extend(reddit_posts)
                logging.info(f"Collected {len(reddit_posts)} Reddit posts")
            except Exception as e:
                logging.error(f"Error collecting Reddit data: {e}")

            try:
                youtube_videos = youtube_future.result(timeout=30)
                all_posts.extend(youtube_videos)
                logging.info(f"Collected {len(youtube_videos)} YouTube videos")
            except Exception as e:
                logging.error(f"Error collecting YouTube data: {e}")

        return all_posts

    def process_sentiment_batch(self, posts: List[Dict]) -> List[Dict]:
        """Process sentiment analysis for a batch of posts"""
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
                        'processed_at': datetime.now(),
                        'metadata': {
                            'author_id': post.get('author_id') or post.get('author'),
                            'likes': post.get('likes', 0),
                            'retweets': post.get('retweets', 0),
                            'score': post.get('score', 0)
                        }
                    }
                    sentiment_results.append(result)

            logging.info(f"Processed sentiment for {len(sentiment_results)} posts")

        except Exception as e:
            logging.error(f"Error processing sentiment batch: {e}")

        return sentiment_results

    def store_results(self, raw_posts: List[Dict], sentiment_results: List[Dict]):
        """Store results in MongoDB"""
        try:
            # Store raw posts
            if raw_posts:
                self.db_client.insert_raw_posts(raw_posts)

            # Store sentiment results
            if sentiment_results:
                self.db_client.insert_sentiment_results(sentiment_results)

        except Exception as e:
            logging.error(f"Error storing results: {e}")

    def run_single_cycle(self):
        """Run one cycle of the pipeline"""
        try:
            logging.info("Starting data collection cycle...")

            # Collect data from all sources
            raw_posts = self.collect_data_from_all_sources()

            if raw_posts:
                # Process sentiment analysis
                sentiment_results = self.process_sentiment_batch(raw_posts)

                # Store results in database
                self.store_results(raw_posts, sentiment_results)

                # Generate summary stats
                stats = self.data_processor.aggregate_sentiment_stats(sentiment_results)
                logging.info(f"Cycle completed. Sentiment distribution: {stats}")

            else:
                logging.info("No new posts collected in this cycle")

        except Exception as e:
            logging.error(f"Error in pipeline cycle: {e}")

    def start_streaming(self):
        """Start the real-time streaming pipeline"""
        self.is_running = True
        logging.info("Starting real-time sentiment analysis pipeline...")

        while self.is_running:
            try:
                cycle_start = time.time()

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