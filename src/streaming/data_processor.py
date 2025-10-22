from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
from datetime import datetime
from typing import Dict, List
import json

class DataProcessor:
    def __init__(self):
        self.spark = None
        self.setup_spark()

    def setup_spark(self):
        """Initialize Spark session"""
        try:
            self.spark = SparkSession.builder \
                .appName("SentimentAnalysisStreaming") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .getOrCreate()

            self.spark.sparkContext.setLogLevel("WARN")
            logging.info("Spark session created successfully")

        except Exception as e:
            logging.error(f"Error setting up Spark: {e}")
            raise

    def define_schema(self):
        """Define schema for incoming social media data"""
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
            logging.error(f"Error processing batch data: {e}")
            return []

    def aggregate_sentiment_stats(self, sentiment_results: List[Dict]) -> Dict:
        """Aggregate sentiment statistics using Python"""
        try:
            if not sentiment_results:
                return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

            # Ensure we're working with a list
            if not isinstance(sentiment_results, list):
                logging.error(f"Invalid input type: expected list, got {type(sentiment_results)}")
                return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

            # Count sentiments using simple Python
            counts = {'positive': 0, 'neutral': 0, 'negative': 0}

            for result in sentiment_results:
                if not isinstance(result, dict):
                    logging.warning(f"Skipping non-dict item: {type(result)}")
                    continue

                sentiment_info = result.get('sentiment', {})
                if not isinstance(sentiment_info, dict):
                    logging.warning(f"Sentiment info is not a dict: {type(sentiment_info)}")
                    continue

                label = sentiment_info.get('label', 'neutral')
                if label in counts:
                    counts[label] += 1

            # Calculate percentages - explicitly convert to list to avoid dict_values issues
            total = sum([counts['positive'], counts['neutral'], counts['negative']])
            stats = {
                'positive': round(counts['positive'] / total * 100, 2) if total > 0 else 0,
                'neutral': round(counts['neutral'] / total * 100, 2) if total > 0 else 0,
                'negative': round(counts['negative'] / total * 100, 2) if total > 0 else 0,
                'total': total
            }

            return stats

        except Exception as e:
            logging.error(f"Error aggregating sentiment stats: {e}")
            return {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}

    def filter_trending_topics(self, posts_data: List[Dict], min_mentions: int = 5) -> List[str]:
        """Identify trending topics from posts"""
        try:
            if not posts_data:
                return []

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
            logging.error(f"Error filtering trending topics: {e}")
            return []

    def stop_spark(self):
        """Stop Spark session"""
        if self.spark:
            self.spark.stop()
            logging.info("Spark session stopped")