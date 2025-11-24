from typing import Dict, List
import logging
from datetime import datetime
import builtins

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import *
    from pyspark.sql.types import *
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False
    logging.warning("PySpark not available. Running without Spark support.")

class DataProcessor:
    def __init__(self):
        self.spark = None
        if SPARK_AVAILABLE:
            self.setup_spark()

    def setup_spark(self):
        """Initialize Spark session"""
        if not SPARK_AVAILABLE:
            logging.info("Spark not available, skipping Spark setup")
            return
            
        try:
            self.spark = SparkSession.builder \
                .appName("SentimentAnalysisStreaming") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .getOrCreate()

            self.spark.sparkContext.setLogLevel("WARN")
            logging.info("Spark session created successfully")

        except Exception as e:
            logging.warning(f"Could not set up Spark (continuing without it): {e}")
            self.spark = None

    def define_schema(self):
        """Define schema for incoming social media data"""
        if not SPARK_AVAILABLE:
            return None
            
        return StructType([
            StructField("id", StringType(), True),
            StructField("text", StringType(), True),
            StructField("platform", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("author_id", StringType(), True),
            StructField("likes", IntegerType(), True),
            StructField("retweets", IntegerType(), True),
            StructField("collected_at", TimestampType(), True),
            StructField("keywords", ArrayType(StringType()), True)
        ])

    def process_batch_data(self, posts_data: List[Dict]) -> List[Dict]:
        """Process a batch of social media posts"""
        try:
            if not posts_data:
                return []

            # If Spark is not available or not initialized, use pure Python
            if not SPARK_AVAILABLE or not self.spark:
                return self._process_batch_python(posts_data)

            # Convert to Spark DataFrame
            df = self.spark.createDataFrame(posts_data, schema=self.define_schema())

            # Data cleaning and transformation
            cleaned_df = df.filter(
                (col("text").isNotNull()) &
                (length(col("text")) > 10)  # Filter out very short posts
            ).distinct()  # Remove duplicates

            # Add processing metadata
            processed_df = cleaned_df.withColumn("processing_time", current_timestamp()) \
                                   .withColumn("text_length", length(col("text"))) \
                                   .withColumn("word_count", size(split(col("text"), " ")))

            # Convert back to list of dictionaries
            result = [row.asDict() for row in processed_df.collect()]

            logging.info(f"Processed {len(result)} posts from {len(posts_data)} input posts")
            return result

        except Exception as e:
            logging.error(f"Error processing batch data with Spark: {e}")
            # Fallback to Python processing
            return self._process_batch_python(posts_data)
    
    def _process_batch_python(self, posts_data: List[Dict]) -> List[Dict]:
        """Process batch using pure Python (no Spark)"""
        try:
            result = []
            seen_ids = set()
            
            for post in posts_data:
                # Filter out posts with missing or short text
                text = post.get('text', '')
                if not text or len(text) <= 10:
                    continue
                
                # Remove duplicates
                post_id = post.get('id')
                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                
                # Add processing metadata
                post['processing_time'] = datetime.utcnow().isoformat()
                post['text_length'] = len(text)
                post['word_count'] = len(text.split())
                
                result.append(post)
            
            logging.info(f"Processed {len(result)} posts from {len(posts_data)} input posts (Python mode)")
            return result
            
        except Exception as e:
            logging.error(f"Error processing batch data with Python: {e}")
            return []

    def aggregate_sentiment_stats(self, sentiment_results: List[Dict]) -> Dict:
        """Aggregate sentiment statistics using pure Python (no Spark)"""
        try:
            if not sentiment_results:
                return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

            # Ensure we're working with a list
            if not isinstance(sentiment_results, list):
                logging.error(f"Invalid input type: expected list, got {type(sentiment_results)}")
                return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

            # Count sentiments using simple Python
            positive_count = 0
            neutral_count = 0
            negative_count = 0

            for result in sentiment_results:
                if not isinstance(result, dict):
                    continue

                sentiment_info = result.get('sentiment')
                if not sentiment_info or not isinstance(sentiment_info, dict):
                    continue

                label = sentiment_info.get('label', '').lower()
                
                if label == 'positive':
                    positive_count += 1
                elif label == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1

            # Calculate total
            total = positive_count + neutral_count + negative_count

            # Calculate percentages
            if total > 0:
                stats = {
                    'positive': builtins.round(positive_count / total * 100, 2),
                    'neutral': builtins.round(neutral_count / total * 100, 2),
                    'negative': builtins.round(negative_count / total * 100, 2),
                    'total': total
                }
            else:
                stats = {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

            return stats

        except Exception as e:
            logging.error(f"Error aggregating sentiment stats: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

    def filter_trending_topics(self, posts_data: List[Dict], min_mentions: int = 5) -> List[str]:
        """Identify trending topics from posts"""
        try:
            if not posts_data:
                return []

            # Use Python if Spark is not available
            if not SPARK_AVAILABLE or not self.spark:
                return self._filter_trending_python(posts_data, min_mentions)

            df = self.spark.createDataFrame(posts_data, schema=self.define_schema())

            # Extract hashtags and mentions
            hashtag_df = df.select(
                explode(split(regexp_extract(col("text"), r'#(\w+)', 1), " ")).alias("hashtag")
            ).filter(col("hashtag") != "")

            # Count hashtag frequency
            trending_df = hashtag_df.groupBy("hashtag").count() \
                                  .filter(col("count") >= min_mentions) \
                                  .orderBy(desc("count"))

            trending_topics = [row['hashtag'] for row in trending_df.collect()]

            logging.info(f"Found {len(trending_topics)} trending topics")
            return trending_topics

        except Exception as e:
            logging.error(f"Error filtering trending topics with Spark: {e}")
            return self._filter_trending_python(posts_data, min_mentions)
    
    def _filter_trending_python(self, posts_data: List[Dict], min_mentions: int = 5) -> List[str]:
        """Identify trending topics using pure Python"""
        try:
            import re
            from collections import Counter
            
            hashtags = []
            for post in posts_data:
                text = post.get('text', '')
                # Extract hashtags
                found_hashtags = re.findall(r'#(\w+)', text)
                hashtags.extend(found_hashtags)
            
            # Count and filter by minimum mentions
            hashtag_counts = Counter(hashtags)
            trending_topics = [
                tag for tag, count in hashtag_counts.most_common()
                if count >= min_mentions
            ]
            
            logging.info(f"Found {len(trending_topics)} trending topics (Python mode)")
            return trending_topics
            
        except Exception as e:
            logging.error(f"Error filtering trending topics with Python: {e}")
            return []

    def stop_spark(self):
        """Stop Spark session"""
        if self.spark:
            self.spark.stop()
            logging.info("Spark session stopped")