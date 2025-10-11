from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import logging
import json

from src.database.mongodb_client import MongoDBClient
from config.settings import Config

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database client
db_client = MongoDBClient()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/sentiment/summary')
def get_sentiment_summary():
    """Get current sentiment summary"""
    platform = request.args.get('platform')
    hours = int(request.args.get('hours', 24))

    try:
        summary = db_client.get_sentiment_summary(platform=platform, hours=hours)
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting sentiment summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sentiment/trends')
def get_sentiment_trends():
    """Get sentiment trends over time"""
    platform = request.args.get('platform')
    days = int(request.args.get('days', 7))

    try:
        trends = db_client.get_trend_data(platform=platform, days=days)

        # Format data for frontend
        formatted_trends = []
        for item in trends:
            formatted_trends.append({
                'date': item['_id']['date'],
                'hour': item['_id']['hour'],
                'sentiment': item['_id']['sentiment'],
                'count': item['count']
            })

        return jsonify({
            'success': True,
            'data': formatted_trends,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting sentiment trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/top')
def get_top_posts():
    """Get top posts by sentiment"""
    sentiment = request.args.get('sentiment', 'positive')
    platform = request.args.get('platform')
    limit = int(request.args.get('limit', 10))

    try:
        posts = db_client.get_top_posts(sentiment=sentiment, platform=platform, limit=limit)

        # Clean up posts for frontend
        cleaned_posts = []
        for post in posts:
            cleaned_post = {
                'id': str(post.get('_id')),
                'text': post.get('text', '')[:200] + '...' if len(post.get('text', '')) > 200 else post.get('text', ''),
                'platform': post.get('platform'),
                'sentiment': post.get('sentiment'),
                'created_at': post.get('created_at').isoformat() if post.get('created_at') else None,
                'metadata': post.get('metadata', {})
            }
            cleaned_posts.append(cleaned_post)

        return jsonify({
            'success': True,
            'data': cleaned_posts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting top posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/posts/recent')
def get_recent_posts():
    """Get recent posts"""
    platform = request.args.get('platform')
    hours = int(request.args.get('hours', 1))
    limit = int(request.args.get('limit', 50))

    try:
        posts = db_client.get_recent_posts(platform=platform, hours=hours, limit=limit)

        # Clean up posts for frontend
        cleaned_posts = []
        for post in posts:
            cleaned_post = {
                'id': str(post.get('_id')),
                'text': post.get('text', '') or post.get('title', ''),
                'platform': post.get('platform'),
                'created_at': post.get('created_at').isoformat() if post.get('created_at') else None,
                'author': post.get('author_id') or post.get('author'),
                'metrics': {
                    'likes': post.get('likes', 0),
                    'retweets': post.get('retweets', 0),
                    'score': post.get('score', 0)
                }
            }
            cleaned_posts.append(cleaned_post)

        return jsonify({
            'success': True,
            'data': cleaned_posts,
            'count': len(cleaned_posts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting recent posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/overview')
def get_overview_stats():
    """Get overview statistics"""
    try:
        # Get stats for last 24 hours
        twitter_summary = db_client.get_sentiment_summary(platform='twitter', hours=24)
        reddit_summary = db_client.get_sentiment_summary(platform='reddit', hours=24)
        youtube_summary = db_client.get_sentiment_summary(platform='youtube', hours=24)
        overall_summary = db_client.get_sentiment_summary(hours=24)

        stats = {
            'overall': overall_summary,
            'platforms': {
                'twitter': twitter_summary,
                'reddit': reddit_summary,
                'youtube': youtube_summary
            },
            'last_updated': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logging.error(f"Error getting overview stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=Config.FLASK_DEBUG, host='0.0.0.0', port=5000)