# Social Media Sentiment Analysis Dashboard

A real-time sentiment analysis system that tracks public opinion across Twitter, Reddit, and YouTube, displaying interactive visualizations and trends.

## 🎯 Project Overview

This system processes 1,000+ social media posts per day, classifies sentiment with machine learning, and displays real-time results on an interactive dashboard. Built with Apache Spark Streaming, TensorFlow, MongoDB, and D3.js.

## ✨ Key Features

- **Real-time Data Collection**: Continuous monitoring of Twitter, Reddit, and YouTube
- **Sentiment Analysis**: Machine learning-powered sentiment classification
- **Interactive Dashboard**: Live visualizations with D3.js
- **Scalable Architecture**: Apache Spark for big data processing
- **Multiple Deployment Modes**: Dashboard with on-demand or continuous data collection
- **Keyword Management**: Add/remove tracked keywords and trigger collection from the UI

## 🏗️ System Architecture

```
Social Media APIs → Spark Streaming → Sentiment Analysis (TensorFlow) → MongoDB → Web Dashboard (D3.js)
                                                                        ↓
                                                                   Power BI Reports
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (free tier)
- Social Media API keys (Twitter, Reddit, YouTube)

### Installation

1. **Clone and setup environment**:
   ```bash
   git clone <repository>
   cd sentiment_analysis_project
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the system**:
   ```bash
   # Recommended: Dashboard with on-demand data collection
   python main.py --mode dashboard
   # or
   python main.py --mode full

   # Legacy pipeline mode (deprecated - use dashboard instead)
   python main.py --mode pipeline
   ```

4. **Access dashboard**:
   Open http://localhost:5000 in your browser

5. **Run Analysis**:
   - Click the **"Run Analysis"** button
   - Enter keywords you want to track (e.g., "AI, Python, Climate Change")
   - Select time range:
     - **60 seconds** (perfect for live demos! 🎬)
     - 24 hours, 3 days, 7 days, or 30 days
   - Click **"Start Analysis"**
   - Watch the progress in real-time
   - Dashboard automatically refreshes when complete
   - Optional: Use the **"Manage Keywords"** button to edit the default keyword list anytime

## 📋 Configuration

### Environment Variables

Edit `.env` file with your credentials:

```env
# Twitter API
TWITTER_BEARER_TOKEN=your_token_here
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_secret_here

# Reddit API
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here

# YouTube API
YOUTUBE_API_KEY=your_key_here

# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/sentiment_analysis
```

### Keywords Configuration

**Dashboard UI (Recommended)**: Use the "Manage Keywords" button in the dashboard to add, remove, and update tracked keywords in real-time. Changes are saved to MongoDB and picked up by the pipeline automatically.

**Config File (Fallback)**: Modify `config/settings.py` to set default keywords:

```python
DEFAULT_KEYWORDS = ['python', 'AI', 'machine learning']
```

Note: Keywords configured via the dashboard take precedence over config file settings.

## 📊 Data Collection Workflow

The system uses an **intuitive modal-based workflow** for running analyses:

### New Workflow (Recommended)

1. **Start the dashboard**: `python main.py --mode dashboard`
2. **Click "Run Analysis"** - A modal dialog opens
3. **Configure your analysis**:
   - Enter keywords (comma-separated, e.g., "AI, Python, Climate")
   - Select time range:
     - **60 seconds (Demo)** - Perfect for live presentations! 🎬
     - 24 hours, 3 days, 7 days, or 30 days
4. **Start Analysis** - Modal closes, progress bar appears
5. **Watch real-time progress**:
   - "Initializing analysis..."
   - "Collecting data from social media platforms..."
   - "Analysis complete! Dashboard updated."
6. **Dashboard auto-refreshes** with new keyword cards and charts

Need to adjust your defaults first? Click **"Manage Keywords"** to update the saved list that auto-fills each new analysis.

### Benefits of This Workflow

- ✅ **Intuitive**: Clear modal interface for configuration
- ✅ **Flexible**: Specify different keywords for each run
- ✅ **Transparent**: Real-time progress feedback
- ✅ **Efficient**: Only collect data when you need it
- ✅ **Visual**: Keyword cards show sentiment breakdown per topic
- ✅ **Demo-ready**: 60-second option for live presentations

### 🎬 Pro Tips for Live Presentations

**Before Your Demo:**
1. Test your API credentials work
2. Pre-select trending keywords (check Twitter/Reddit for hot topics)
3. Keep browser window at 100% zoom for best visibility
4. Have the dashboard open at http://localhost:5000

**During Your Demo:**
1. Use **60 seconds** time range for instant results
2. Choose 2-3 high-activity keywords (e.g., "AI", "Python", "Tech")
3. Show the modal → Start analysis → Watch progress in real-time
4. While waiting (~30-45 seconds), explain the architecture
5. Dashboard auto-refreshes when complete - wow factor! ✨

**Backup Plan:**
- If live collection is slow, use **24 hours** range with pre-existing data
- Have a rehearsal run 5 minutes before presenting

**For continuous collection** (advanced use):
You can modify the `/api/pipeline/run_once` endpoint to run on a schedule using a task scheduler (cron, Windows Task Scheduler, or Celery).

## 🔧 API Setup Guide

### Twitter API Setup
1. Create a Twitter Developer account
2. Create a new App
3. Generate Bearer Token and API keys
4. Add to `.env` file

### Reddit API Setup
1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (script type)
3. Note the client ID and secret
4. Add to `.env` file

### YouTube API Setup
1. Go to Google Cloud Console
2. Enable YouTube Data API v3
3. Create API key
4. Add to `.env` file

### MongoDB Setup
1. Create MongoDB Atlas account
2. Create a cluster (free tier)
3. Create database user
4. Get connection string
5. Add to `.env` file

## 📊 Dashboard Features

The web dashboard provides:

- **Keyword Cards**: Individual sentiment analytics for each tracked keyword
- **Real-time sentiment overview**: Positive, neutral, negative percentages
- **Trend charts**: Sentiment changes over time
- **Platform breakdown**: Twitter, Reddit, YouTube statistics
- **Top posts**: Highest confidence posts by sentiment
- **Auto-refresh**: Updates every 30 seconds

### Keyword-Based Analytics

Each tracked keyword gets its own analytics card showing:
- Sentiment distribution (positive/neutral/negative %)
- Total posts collected for that keyword
- Visual progress bars for easy comparison
- Click any card to filter the entire dashboard to that keyword

This makes it easy to:
- Compare sentiment across different topics
- Track individual keyword performance
- Identify which topics generate more engagement
- Spot trends in specific areas of interest

### Dashboard Controls

- **Refresh Button**: Manual data refresh
- **Manage Keywords**: Add, remove, or update tracked keywords in real-time
- **Run Fetch Now**: Trigger immediate data collection with current keywords
- **Keyword Cards**: Click any card to filter dashboard by that keyword
- **Filter by Keyword**: Dropdown to manually select keyword filter
- **Time Period Selector**: Choose trend analysis period
- **Date Range Filter**: Filter data by custom start/end dates
- **Platform Filters**: View specific platform data

## 🛠️ Development

### Project Structure

```
sentiment_analysis_project/
├── src/
│   ├── data_collection/     # Social media API clients
│   ├── sentiment_analysis/  # ML models and text processing
│   ├── database/           # MongoDB connection and schemas
│   ├── streaming/          # Spark streaming pipeline
│   ├── dashboard/          # Flask web app and frontend
│   └── utils/             # Logging, monitoring, error handling
├── config/                # Configuration settings
├── tests/                 # Unit tests
├── docs/                  # Additional documentation
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

### Adding New Data Sources

1. Create collector class in `src/data_collection/`
2. Implement data collection methods
3. Add to pipeline in `src/streaming/real_time_pipeline.py`
4. Update dashboard API if needed

### Customizing Sentiment Analysis

1. Train new model in `src/sentiment_analysis/sentiment_analyzer.py`
2. Replace TextBlob with custom TensorFlow model
3. Adjust confidence thresholds
4. Add new sentiment categories

## 📈 Monitoring & Maintenance

### System Status

Check system health:
```bash
python main.py --mode status
```

### Log Files

- `logs/sentiment_analysis.log`: General application logs
- `logs/errors.log`: Error-specific logs

### Performance Monitoring

The system tracks:
- CPU and memory usage
- Processing times
- Error rates
- API response times

### Database Maintenance

Clean old data:
```python
from src.database.mongodb_client import MongoDBClient
db = MongoDBClient()
db.cleanup_old_data(days=30)  # Remove data older than 30 days
```

## 🧪 Testing

Run tests:
```bash
python -m pytest tests/
```

Create test data:
```bash
python tests/create_test_data.py
```

## 📚 API Documentation

### REST Endpoints

- `GET /api/sentiment/summary`: Current sentiment statistics
- `GET /api/sentiment/trends`: Historical trend data
- `GET /api/sentiment/by-keywords`: Sentiment statistics grouped by keyword
- `GET /api/posts/top`: Top posts by sentiment
- `GET /api/posts/recent`: Recent posts
- `GET /api/stats/overview`: System overview
- `GET /api/config/keywords`: Get active keywords
- `POST /api/config/keywords`: Update active keywords (body: `{"keywords": ["word1", "word2"]}`)
- `POST /api/pipeline/run_once`: Trigger immediate data collection cycle

### Query Parameters

All data retrieval endpoints support the following filters:

- `platform`: Filter by platform (twitter, reddit, youtube)
- `keyword`: Filter by specific keyword (e.g., `?keyword=AI`)
- `hours`: Time range in hours (default: 24)
- `days`: Time range in days for trends (default: 7)
- `start_date`: Start datetime in ISO format (e.g., `2025-11-01T00:00:00Z`)
- `end_date`: End datetime in ISO format (e.g., `2025-11-24T23:59:59Z`)
- `limit`: Number of results (default: 10)

**Example**: Get sentiment summary for "AI" keyword from Twitter in the last 48 hours:
```
GET /api/sentiment/summary?keyword=AI&platform=twitter&hours=48
```

## 🚨 Troubleshooting

### Common Issues

**API Rate Limits**:
- Twitter: 300 requests/15 minutes
- Reddit: 60 requests/minute
- YouTube: 10,000 units/day

**Database Connection**:
- Check MongoDB URI format
- Verify network access (whitelist IP)
- Confirm credentials

**Dashboard Not Loading**:
- Check Flask is running on port 5000
- Verify no firewall blocking
- Check browser console for errors

**No Data Collection**:
- Verify API keys are correct
- Check internet connectivity
- Review error logs

### Debug Mode

Run with debug logging:
```bash
python main.py --mode full --log-level DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is for educational purposes. Ensure compliance with social media platform terms of service.

## 📞 Support

For issues and questions:
1. Check troubleshooting section
2. Review log files
3. Create GitHub issue
4. Contact development team

---

**Note**: This system is designed for academic and learning purposes. Always respect social media platform rate limits and terms of service.