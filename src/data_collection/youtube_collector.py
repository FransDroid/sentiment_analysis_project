from googleapiclient.discovery import build
import logging
from datetime import datetime
from typing import List, Dict
from config.settings import Config

class YouTubeCollector:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)

    def search_videos(self, keywords: List[str], max_results: int = 50) -> List[Dict]:
        """Search for YouTube videos based on keywords"""
        videos_data = []

        try:
            query = " OR ".join(keywords)
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                order='relevance'
            ).execute()

            for item in search_response['items']:
                video_data = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00')),
                    'platform': 'youtube',
                    'collected_at': datetime.now(),
                    'keywords': keywords
                }
                videos_data.append(video_data)

        except Exception as e:
            logging.error(f"Error searching YouTube videos: {e}")

        return videos_data

    def collect_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """Collect comments from a YouTube video"""
        comments_data = []

        try:
            comments_response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                order='relevance'
            ).execute()

            for item in comments_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'id': item['snippet']['topLevelComment']['id'],
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'created_at': datetime.fromisoformat(comment['publishedAt'].replace('Z', '+00:00')),
                    'likes': comment['likeCount'],
                    'platform': 'youtube',
                    'video_id': video_id,
                    'collected_at': datetime.now()
                }
                comments_data.append(comment_data)

        except Exception as e:
            logging.error(f"Error collecting YouTube comments: {e}")

        return comments_data

    def get_video_stats(self, video_id: str) -> Dict:
        """Get video statistics"""
        try:
            stats_response = self.youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()

            if stats_response['items']:
                stats = stats_response['items'][0]['statistics']
                return {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0))
                }

        except Exception as e:
            logging.error(f"Error getting video stats: {e}")

        return {}