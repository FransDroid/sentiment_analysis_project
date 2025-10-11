import praw
import logging
from datetime import datetime
from typing import List, Dict
from config.settings import Config

class RedditCollector:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT
        )

    def collect_posts(self, subreddits: List[str], keywords: List[str], limit: int = 100) -> List[Dict]:
        """Collect Reddit posts from specified subreddits"""
        posts_data = []

        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)

                # Search for posts with keywords
                for keyword in keywords:
                    search_results = subreddit.search(keyword, limit=limit//len(keywords))

                    for submission in search_results:
                        post_data = {
                            'id': submission.id,
                            'title': submission.title,
                            'text': submission.selftext,
                            'created_at': datetime.fromtimestamp(submission.created_utc),
                            'author': str(submission.author) if submission.author else '[deleted]',
                            'platform': 'reddit',
                            'subreddit': subreddit_name,
                            'upvotes': submission.ups,
                            'downvotes': submission.downs,
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'collected_at': datetime.now(),
                            'keywords': keywords
                        }
                        posts_data.append(post_data)

        except Exception as e:
            logging.error(f"Error collecting Reddit posts: {e}")

        return posts_data

    def collect_comments(self, submission_id: str, limit: int = 50) -> List[Dict]:
        """Collect comments from a specific Reddit post"""
        comments_data = []

        try:
            submission = self.reddit.submission(id=submission_id)
            submission.comments.replace_more(limit=0)

            for comment in submission.comments.list()[:limit]:
                comment_data = {
                    'id': comment.id,
                    'text': comment.body,
                    'created_at': datetime.fromtimestamp(comment.created_utc),
                    'author': str(comment.author) if comment.author else '[deleted]',
                    'platform': 'reddit',
                    'parent_id': submission_id,
                    'score': comment.score,
                    'collected_at': datetime.now()
                }
                comments_data.append(comment_data)

        except Exception as e:
            logging.error(f"Error collecting Reddit comments: {e}")

        return comments_data