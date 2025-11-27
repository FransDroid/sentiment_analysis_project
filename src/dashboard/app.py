from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import logging
import json
import threading
import uuid

from src.database.mongodb_client import MongoDBClient
from src.streaming.real_time_pipeline import RealTimePipeline
from src.utils.error_handler import parse_date_param, validate_date_range
from config.settings import Config

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize database client
db_client = MongoDBClient()

# Global analysis status tracking
analysis_status = {
    'status': 'idle',  # idle, running, completed, error
    'progress': '',
    'message': '',
    'run_id': None,
    'keywords': [],
    'duration_days': None,
    'stats': None,
    'raw_posts_count': 0,
    'sentiment_results_count': 0,
    'started_at': None,
    'completed_at': None,
    'window_start': None,
    'window_end': None
}

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
    keyword = request.args.get('keyword')
    run_id = request.args.get('run_id')

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
            end_dt=end_dt,
            keyword=keyword,
            run_id=run_id
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
    keyword = request.args.get('keyword')
    run_id = request.args.get('run_id')

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
            end_dt=end_dt,
            keyword=keyword,
            run_id=run_id
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
    keyword = request.args.get('keyword')
    run_id = request.args.get('run_id')

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
            end_dt=end_dt,
            keyword=keyword,
            run_id=run_id
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
    keyword = request.args.get('keyword')
    run_id = request.args.get('run_id')
    
    try:
        # Get stats for last 24 hours
        twitter_summary = db_client.get_sentiment_summary(platform='twitter', hours=24, keyword=keyword, run_id=run_id)
        reddit_summary = db_client.get_sentiment_summary(platform='reddit', hours=24, keyword=keyword, run_id=run_id)
        youtube_summary = db_client.get_sentiment_summary(platform='youtube', hours=24, keyword=keyword, run_id=run_id)
        overall_summary = db_client.get_sentiment_summary(hours=24, keyword=keyword, run_id=run_id)

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

@app.route('/api/sentiment/by-keywords')
def get_sentiment_by_keywords():
    """Get sentiment statistics grouped by keyword"""
    try:
        hours = int(request.args.get('hours', 24))
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        run_id = request.args.get('run_id')
        
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
        
        keyword_data = db_client.get_sentiment_by_keywords(
            hours=hours,
            start_dt=start_dt,
            end_dt=end_dt,
            run_id=run_id
        )
        
        return jsonify({
            'success': True,
            'data': keyword_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except ValueError as e:
        logging.warning(f"Invalid parameter: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logging.error(f"Error getting sentiment by keywords: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route("/api/pipeline/run_once", methods=['POST'])
def run_once():
    """Start an analysis run with specified keywords and duration"""
    global analysis_status
    
    # Check if analysis is already running
    if analysis_status['status'] == 'running':
        return jsonify({
            'success': False,
            'message': 'Analysis is already running'
        }), 409
    
    try:
        # Get request data
        data = request.get_json() or {}
        keywords = data.get('keywords', [])
        duration_days = float(data.get('duration_days', 1))
        
        # Validate inputs
        if not keywords or not isinstance(keywords, list):
            return jsonify({
                'success': False,
                'message': 'Keywords must be provided as a list'
            }), 400
        
        run_id = str(uuid.uuid4())

        try:
            db_client.create_run_record(run_id, keywords, duration_days)
        except Exception as rec_error:
            logging.error(f"Unable to create run record: {rec_error}")

        # Update in-memory status
        analysis_status['status'] = 'queued'
        analysis_status['progress'] = 'Queued for execution'
        analysis_status['message'] = ''
        analysis_status['run_id'] = run_id
        analysis_status['keywords'] = keywords
        analysis_status['duration_days'] = duration_days
        analysis_status['stats'] = None
        analysis_status['raw_posts_count'] = 0
        analysis_status['sentiment_results_count'] = 0
        analysis_status['started_at'] = None
        analysis_status['completed_at'] = None
        analysis_status['window_start'] = None
        analysis_status['window_end'] = None
        
        # Run analysis in background thread
        def run_analysis():
            global analysis_status
            try:
                analysis_status['status'] = 'running'
                analysis_status['progress'] = 'Collecting data from social media platforms...'
                analysis_status['message'] = ''
                started_at = datetime.now(timezone.utc)
                analysis_status['started_at'] = started_at.isoformat()

                try:
                    db_client.update_run_record(
                        run_id,
                        status='running',
                        progress=analysis_status['progress'],
                        started_at=started_at
                    )
                except Exception as update_error:
                    logging.error(f"Unable to update run record to running: {update_error}")

                # Create pipeline and run with parameters
                pipeline = RealTimePipeline()
                result = pipeline.run_single_cycle_once(keywords=keywords, duration_days=duration_days, run_id=run_id)
                stats = result.get('stats', {}) if isinstance(result, dict) else {}
                raw_posts_count = result.get('raw_posts_count', 0) if isinstance(result, dict) else 0
                sentiment_results_count = result.get('sentiment_results_count', 0) if isinstance(result, dict) else 0
                time_window = result.get('time_window', {}) if isinstance(result, dict) else {}
                window_start = time_window.get('start')
                window_end = time_window.get('end')
                
                # Mark as completed
                analysis_status['status'] = 'completed'
                analysis_status['progress'] = 'Analysis completed successfully'
                analysis_status['stats'] = stats
                analysis_status['raw_posts_count'] = raw_posts_count
                analysis_status['sentiment_results_count'] = sentiment_results_count
                completed_at = datetime.now(timezone.utc)
                analysis_status['completed_at'] = completed_at.isoformat()
                analysis_status['window_start'] = window_start.isoformat() if isinstance(window_start, datetime) else None
                analysis_status['window_end'] = window_end.isoformat() if isinstance(window_end, datetime) else None

                try:
                    db_client.update_run_record(
                        run_id,
                        status='completed',
                        progress=analysis_status['progress'],
                        completed_at=completed_at,
                        stats=stats,
                        raw_posts_count=raw_posts_count,
                        sentiment_results_count=sentiment_results_count,
                        window_start=window_start,
                        window_end=window_end
                    )
                except Exception as final_update_error:
                    logging.error(f"Unable to finalize run record {run_id}: {final_update_error}")
                
            except Exception as e:
                logging.error(f"Analysis error: {e}")
                analysis_status['status'] = 'error'
                analysis_status['message'] = str(e)
                completed_at = datetime.now(timezone.utc)
                analysis_status['completed_at'] = completed_at.isoformat()
                analysis_status['window_start'] = None
                analysis_status['window_end'] = None
                try:
                    db_client.update_run_record(
                        run_id,
                        status='error',
                        progress='Analysis failed',
                        completed_at=completed_at,
                        message=str(e)
                    )
                except Exception as error_update_error:
                    logging.error(f"Unable to mark run record {run_id} as failed: {error_update_error}")

        # Start thread
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': run_id,
            'message': 'Analysis started'
        })
        
    except Exception as e:
        logging.error(f"Error starting analysis: {e}")
        analysis_status['status'] = 'error'
        analysis_status['message'] = str(e)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route("/api/pipeline/status", methods=['GET'])
def pipeline_status():
    """Get current analysis status"""
    global analysis_status
    
    return jsonify({
        'success': True,
        'status': analysis_status['status'],
        'progress': analysis_status['progress'],
        'message': analysis_status['message'],
        'run_id': analysis_status['run_id'],
        'keywords': analysis_status['keywords'],
        'duration_days': analysis_status['duration_days'],
        'stats': analysis_status['stats'],
        'raw_posts_count': analysis_status['raw_posts_count'],
        'sentiment_results_count': analysis_status['sentiment_results_count'],
        'started_at': analysis_status['started_at'],
        'completed_at': analysis_status['completed_at'],
        'window_start': analysis_status['window_start'],
        'window_end': analysis_status['window_end']
    })

@app.errorhandler(404)

def _serialize_run(run_doc):
    def serialize_dt(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    return {
        'run_id': run_doc.get('_id'),
        'keywords': run_doc.get('keywords', []),
        'duration_days': run_doc.get('duration_days'),
        'status': run_doc.get('status'),
        'progress': run_doc.get('progress'),
        'created_at': serialize_dt(run_doc.get('created_at')),
        'started_at': serialize_dt(run_doc.get('started_at')),
        'completed_at': serialize_dt(run_doc.get('completed_at')),
        'window_start': serialize_dt(run_doc.get('window_start')),
        'window_end': serialize_dt(run_doc.get('window_end')),
        'stats': run_doc.get('stats'),
        'raw_posts_count': run_doc.get('raw_posts_count', 0),
        'sentiment_results_count': run_doc.get('sentiment_results_count', 0),
        'message': run_doc.get('message'),
    }


@app.route("/api/pipeline/runs", methods=['GET'])
def list_pipeline_runs():
    try:
        limit = int(request.args.get('limit', 20))
        limit = max(1, min(limit, 50))
        runs = db_client.get_recent_runs(limit=limit)
        return jsonify({
            'success': True,
            'data': [_serialize_run(run) for run in runs]
        })
    except Exception as e:
        logging.error(f"Error listing pipeline runs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/api/pipeline/runs/<run_id>", methods=['GET'])
def get_pipeline_run(run_id):
    try:
        run = db_client.get_run_by_id(run_id)
        if not run:
            return jsonify({'success': False, 'error': 'Run not found'}), 404

        return jsonify({'success': True, 'data': _serialize_run(run)})
    except Exception as e:
        logging.error(f"Error fetching pipeline run {run_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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