from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import logging
import json

from src.database.mongodb_client import MongoDBClient
from src.utils.error_handler import parse_date_param, validate_date_range
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
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        # Parse date parameters if provided
        start_dt = None
        end_dt = None
        
        if start_date_str:
            start_dt = parse_date_param(start_date_str, 'start_date')
        if end_date_str:
            end_dt = parse_date_param(end_date_str, 'end_date')
        
        # Validate date range
        if start_dt or end_dt:
            validate_date_range(start_dt, end_dt, Config.MAX_DATE_RANGE_DAYS)
        
        summary = db_client.get_sentiment_summary(
            platform=platform, 
            hours=hours,
            start_dt=start_dt,
            end_dt=end_dt
        )
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except ValueError as e:
        logging.warning(f"Invalid date parameter: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
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
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        # Parse date parameters if provided
        start_dt = None
        end_dt = None
        
        if start_date_str:
            start_dt = parse_date_param(start_date_str, 'start_date')
        if end_date_str:
            end_dt = parse_date_param(end_date_str, 'end_date')
        
        # Validate date range
        if start_dt or end_dt:
            validate_date_range(start_dt, end_dt, Config.MAX_DATE_RANGE_DAYS)
        
        trends = db_client.get_trend_data(
            platform=platform, 
            days=days,
            start_dt=start_dt,
            end_dt=end_dt
        )

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
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except ValueError as e:
        logging.warning(f"Invalid date parameter: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
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
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        # Parse date parameters if provided
        start_dt = None
        end_dt = None
        
        if start_date_str:
            start_dt = parse_date_param(start_date_str, 'start_date')
        if end_date_str:
            end_dt = parse_date_param(end_date_str, 'end_date')
        
        # Validate date range
        if start_dt or end_dt:
            validate_date_range(start_dt, end_dt, Config.MAX_DATE_RANGE_DAYS)
        
        posts = db_client.get_top_posts(
            sentiment=sentiment, 
            platform=platform, 
            limit=limit,
            start_dt=start_dt,
            end_dt=end_dt
        )

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
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except ValueError as e:
        logging.warning(f"Invalid date parameter: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
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
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        # Parse date parameters if provided
        start_dt = None
        end_dt = None
        
        if start_date_str:
            start_dt = parse_date_param(start_date_str, 'start_date')
        if end_date_str:
            end_dt = parse_date_param(end_date_str, 'end_date')
        
        # Validate date range
        if start_dt or end_dt:
            validate_date_range(start_dt, end_dt, Config.MAX_DATE_RANGE_DAYS)
        
        posts = db_client.get_recent_posts(
            platform=platform, 
            hours=hours, 
            limit=limit,
            start_dt=start_dt,
            end_dt=end_dt
        )

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
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except ValueError as e:
        logging.warning(f"Invalid date parameter: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
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

@app.route('/api/config/keywords')
def get_configured_keywords():
    """Get configured keywords for monitoring"""
    try:
        keywords = db_client.get_active_keywords()
        return jsonify({
            'success': True,
            'data': keywords
        })
    except Exception as e:
        logging.error(f"Error getting configured keywords: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config/keywords', methods=['POST'])
def update_configured_keywords():
    """Update configured keywords for monitoring"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        keywords = list(set([kw.strip() for kw in keywords if kw.strip()]))

        if len(keywords) == 0:
            raise ValueError("Keyword list cannot be empty")

        for keyword in keywords:
            if not keyword.isalpha():
                raise ValueError("Keywords must be alphabetic strings only")

        if len(keywords) > 50:
            raise ValueError("Cannot have more than 50 keywords")

        db_client.set_active_keywords(keywords)
        return jsonify({
            'success': True,
            'message': 'Keywords updated successfully'
        })
    except Exception as e:
        logging.error(f"Error updating configured keywords: {e}")
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